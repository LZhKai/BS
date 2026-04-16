"""
Vehicle monitor streaming using Spark Structured Streaming.

Pipeline:
- append_event() receives per-frame detection events into a memory queue
- A flush thread periodically writes queued events as JSON files to a staging directory
- Spark Structured Streaming ingests new JSON files via readStream
- foreachBatch computes aggregate metrics over a sliding time window
- Metrics are pushed to the frontend via Socket.IO callback
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import time
from collections import deque
from datetime import datetime
from typing import Callable, Deque, Dict, List, Optional

from config import Config

try:
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark.sql.types import (
        DoubleType,
        IntegerType,
        StringType,
        StructField,
        StructType,
    )

    SPARK_AVAILABLE = True
except Exception:
    SparkSession = None
    F = None
    SPARK_AVAILABLE = False


MonitorEvent = Dict[str, object]
MetricsCallback = Callable[[Dict[str, object]], None]

_EVENT_SCHEMA: Optional[StructType] = None
if SPARK_AVAILABLE:
    _EVENT_SCHEMA = StructType([
        StructField("ts", DoubleType(), True),
        StructField("track_id", IntegerType(), True),
        StructField("vehicle_type", StringType(), True),
        StructField("confidence", DoubleType(), True),
        StructField("frame_id", IntegerType(), True),
    ])


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class MonitorSparkStreamer:
    """Structured Streaming based vehicle detection event aggregator."""

    def __init__(self, batch_seconds: int, window_seconds: int):
        self.batch_seconds = max(1, int(batch_seconds))
        self.window_seconds = max(self.batch_seconds, int(window_seconds))
        self.spark: Optional["SparkSession"] = None
        self._running = False
        self._query = None
        self._flush_thread: Optional[threading.Thread] = None
        self._event_queue: Deque[MonitorEvent] = deque()
        self._window_events: Deque[MonitorEvent] = deque()
        self._lock = threading.Lock()
        self._latest_metrics: Optional[Dict[str, object]] = None
        self._on_metrics: Optional[MetricsCallback] = None
        self._stream_dir: Optional[str] = None
        self._file_counter = 0

    @property
    def available(self) -> bool:
        return SPARK_AVAILABLE

    def set_on_metrics(self, callback: Optional[MetricsCallback]):
        self._on_metrics = callback

    def start(self) -> bool:
        if not SPARK_AVAILABLE:
            return False
        if self._running:
            return True

        if self.spark is None:
            self.spark = (
                SparkSession.builder
                .appName("VehicleMonitorStructuredStreaming")
                .master("local[2]")
                .config("spark.ui.enabled", "false")
                .config("spark.sql.streaming.schemaInference", "false")
                .getOrCreate()
            )
            self.spark.sparkContext.setLogLevel("ERROR")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._stream_dir = os.path.join(base_dir, "_stream_input")
        if os.path.exists(self._stream_dir):
            shutil.rmtree(self._stream_dir)
        os.makedirs(self._stream_dir, exist_ok=True)

        self._running = True

        stream_df = (
            self.spark.readStream
            .format("json")
            .schema(_EVENT_SCHEMA)
            .load(self._stream_dir)
        )

        self._query = (
            stream_df.writeStream
            .foreachBatch(self._process_batch)
            .trigger(processingTime=f"{self.batch_seconds} seconds")
            .start()
        )

        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

        print(
            f"Structured Streaming started "
            f"(batch={self.batch_seconds}s, window={self.window_seconds}s)"
        )
        return True

    def stop(self):
        self._running = False

        if self._query is not None:
            try:
                self._query.stop()
            except Exception as e:
                print(f"Error stopping streaming query: {e}")
            self._query = None

        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=self.batch_seconds + 2)
        self._flush_thread = None

        with self._lock:
            self._event_queue.clear()
            self._window_events.clear()

        if self._stream_dir and os.path.exists(self._stream_dir):
            try:
                shutil.rmtree(self._stream_dir)
            except Exception:
                pass

        print("Structured Streaming stopped")

    def append_event(self, event: MonitorEvent):
        if not self._running:
            return
        with self._lock:
            self._event_queue.append(event)
            if len(self._event_queue) > 10000:
                self._event_queue.popleft()

    def get_latest_metrics(self) -> Optional[Dict[str, object]]:
        with self._lock:
            if self._latest_metrics is None:
                return None
            return dict(self._latest_metrics)

    # ------------------------------------------------------------------ #
    #  Flush thread: queue -> JSON files on disk for Spark to ingest      #
    # ------------------------------------------------------------------ #

    def _flush_loop(self):
        """Drain the event queue and write JSON files for Spark readStream."""
        while self._running:
            time.sleep(max(1, self.batch_seconds // 2))
            events = self._drain_queue()
            if events:
                self._write_json_batch(events)
            self._cleanup_old_files()

    def _drain_queue(self) -> List[MonitorEvent]:
        drained: List[MonitorEvent] = []
        with self._lock:
            while self._event_queue:
                drained.append(self._event_queue.popleft())
        return drained

    def _write_json_batch(self, events: List[MonitorEvent]):
        if not self._stream_dir:
            return
        self._file_counter += 1
        ts_ms = int(time.time() * 1000)
        tmp_name = f".tmp_batch_{ts_ms}_{self._file_counter}.json"
        final_name = f"batch_{ts_ms}_{self._file_counter}.json"
        tmp_path = os.path.join(self._stream_dir, tmp_name)
        final_path = os.path.join(self._stream_dir, final_name)
        try:
            with open(tmp_path, "w") as f:
                for evt in events:
                    f.write(json.dumps(evt) + "\n")
            os.replace(tmp_path, final_path)
        except Exception as e:
            print(f"Failed to write event batch: {e}")

    def _cleanup_old_files(self):
        """Remove ingested JSON files older than 2x window to prevent disk growth."""
        if not self._stream_dir:
            return
        cutoff = time.time() - self.window_seconds * 2
        try:
            for fname in os.listdir(self._stream_dir):
                if fname.startswith("."):
                    continue
                fpath = os.path.join(self._stream_dir, fname)
                if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                    os.remove(fpath)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Structured Streaming foreachBatch callback                         #
    # ------------------------------------------------------------------ #

    def _process_batch(self, batch_df, batch_id):
        """Called by Spark Structured Streaming for each micro-batch."""
        try:
            if batch_df.head(1) is None or len(batch_df.head(1)) == 0:
                return
        except Exception:
            return

        now_ts = time.time()

        try:
            new_rows = batch_df.collect()
        except Exception as e:
            print(f"Failed to collect batch {batch_id}: {e}")
            return

        with self._lock:
            for row in new_rows:
                self._window_events.append(row.asDict())
            while (
                self._window_events
                and _safe_float(self._window_events[0].get("ts"))
                < (now_ts - self.window_seconds)
            ):
                self._window_events.popleft()
            window_snapshot = list(self._window_events)

        if not window_snapshot:
            return

        metrics = self._aggregate(window_snapshot)
        metrics["batchSeconds"] = self.batch_seconds
        metrics["windowSeconds"] = self.window_seconds
        metrics["timestamp"] = datetime.now().isoformat()

        with self._lock:
            self._latest_metrics = metrics

        if self._on_metrics:
            try:
                self._on_metrics(metrics)
            except Exception as e:
                print(f"Failed to emit monitor metrics: {e}")

    def _aggregate(self, events: List[Dict]) -> Dict[str, object]:
        """Compute aggregate metrics from windowed events using Spark."""
        if not events:
            return {
                "totalCount": 0,
                "currentHourCount": 0,
                "todayCount": 0,
                "uniqueTrackCount": 0,
                "unique_by_type": {
                    "car": 0, "truck": 0, "bus": 0, "motorcycle": 0
                },
                "avgConfidence": 0.0,
            }

        df = self.spark.createDataFrame(events, schema=_EVENT_SCHEMA)

        total_count = df.count()
        unique_track_count = df.select("track_id").distinct().count()
        avg_conf = (
            df.agg(F.avg(F.col("confidence")).alias("avg_conf"))
            .collect()[0]["avg_conf"]
            or 0.0
        )

        type_counts = {"car": 0, "truck": 0, "bus": 0, "motorcycle": 0}
        for row in df.groupBy("vehicle_type").count().collect():
            vtype = str(row["vehicle_type"] or "unknown").lower()
            if vtype in type_counts:
                type_counts[vtype] = int(row["count"] or 0)

        return {
            "totalCount": int(total_count),
            "currentHourCount": int(total_count),
            "todayCount": int(unique_track_count),
            "uniqueTrackCount": int(unique_track_count),
            "unique_by_type": type_counts,
            "avgConfidence": _safe_float(avg_conf),
        }


monitor_streamer = MonitorSparkStreamer(
    batch_seconds=getattr(Config, "MONITOR_STREAM_BATCH_SECONDS", 5),
    window_seconds=getattr(Config, "MONITOR_STREAM_WINDOW_SECONDS", 30),
)
