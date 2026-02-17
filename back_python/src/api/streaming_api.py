"""
Real-time streaming API.
"""
import os
from datetime import datetime
import threading

from flask import Blueprint, jsonify
from flask_socketio import emit

from config import Config
from src.utils.database import execute_insert, execute_update

# Optional import: Spark Streaming
SPARK_AVAILABLE = False
VehicleStreamingProcessor = None

try:
    from src.streaming.spark_streaming import VehicleStreamingProcessor
    SPARK_AVAILABLE = True
except ImportError:
    pass
except Exception as e:
    print(f"Warning: failed to load Spark Streaming module: {e}")

streaming_bp = Blueprint('streaming', __name__)

# Global state
socketio_instance = None
streaming_processor = None
streaming_thread = None
stats_lock = threading.Lock()
traffic_stats = {
    'today_count': 0,
    'current_hour_count': 0,
    'entry_count': 0,
    'exit_count': 0,
    'last_timestamp': None
}
PERSIST_MODE = os.getenv('TRAFFIC_STAT_PERSIST_MODE', 'minute').strip().lower()
persist_state = {
    'minute_bucket': None,
    'minute_entry': 0,
    'minute_exit': 0,
    'session_entry': 0,
    'session_exit': 0
}


def _init_traffic_flow_table():
    execute_update(
        """
        CREATE TABLE IF NOT EXISTS traffic_flow_stat (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            stat_time DATETIME NOT NULL,
            entry_count INT NOT NULL DEFAULT 0,
            exit_count INT NOT NULL DEFAULT 0,
            total_count INT NOT NULL DEFAULT 0,
            source VARCHAR(32) DEFAULT 'realtime',
            remark VARCHAR(255) DEFAULT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_stat_time (stat_time),
            KEY idx_create_time (create_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def _to_mysql_datetime(ts: str) -> str:
    if not ts:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txt = ts.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _to_minute_bucket(ts: str) -> str:
    txt = (ts or '').strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        dt = datetime.now()
    dt = dt.replace(second=0, microsecond=0)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _save_traffic_flow_stat(ts: str, entry: int, exit_v: int, total: int):
    try:
        execute_insert(
            """
            INSERT INTO traffic_flow_stat
            (stat_time, entry_count, exit_count, total_count, source)
            VALUES (:stat_time, :entry_count, :exit_count, :total_count, :source)
            """,
            {
                "stat_time": _to_mysql_datetime(ts),
                "entry_count": entry,
                "exit_count": exit_v,
                "total_count": total,
                "source": "realtime",
            },
        )
    except Exception as e:
        print(f"Warning: failed to persist traffic_flow_stat: {e}")


def flush_traffic_persistence(timestamp=None):
    """Flush aggregated traffic stats to DB (used on stop/eof)."""
    ts = _normalize_timestamp(timestamp)
    with stats_lock:
        if PERSIST_MODE == 'minute':
            bucket = persist_state['minute_bucket']
            entry = persist_state['minute_entry']
            exit_v = persist_state['minute_exit']
            persist_state['minute_bucket'] = None
            persist_state['minute_entry'] = 0
            persist_state['minute_exit'] = 0
            if bucket and (entry > 0 or exit_v > 0):
                _save_traffic_flow_stat(
                    ts=bucket,
                    entry=entry,
                    exit_v=exit_v,
                    total=entry + exit_v
                )
        elif PERSIST_MODE == 'video_end':
            entry = persist_state['session_entry']
            exit_v = persist_state['session_exit']
            persist_state['session_entry'] = 0
            persist_state['session_exit'] = 0
            if entry > 0 or exit_v > 0:
                _save_traffic_flow_stat(
                    ts=ts,
                    entry=entry,
                    exit_v=exit_v,
                    total=entry + exit_v
                )


def _normalize_timestamp(ts=None):
    if ts is None:
        return datetime.now().isoformat()
    if isinstance(ts, str) and ts.strip():
        return ts
    return datetime.now().isoformat()


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def update_traffic_stats(entry_count=0, exit_count=0, timestamp=None):
    """Update in-memory traffic stats and return websocket payload (camelCase)."""
    entry = max(0, _to_int(entry_count))
    exit_v = max(0, _to_int(exit_count))
    ts = _normalize_timestamp(timestamp)

    with stats_lock:
        traffic_stats['entry_count'] += entry
        traffic_stats['exit_count'] += exit_v
        traffic_stats['today_count'] = traffic_stats['entry_count'] + traffic_stats['exit_count']
        traffic_stats['current_hour_count'] = entry + exit_v
        traffic_stats['last_timestamp'] = ts
        today_count = traffic_stats['today_count']
        current_hour_count = traffic_stats['current_hour_count']
        if PERSIST_MODE == 'realtime':
            _save_traffic_flow_stat(ts=ts, entry=entry, exit_v=exit_v, total=entry + exit_v)
        elif PERSIST_MODE == 'minute':
            bucket = _to_minute_bucket(ts)
            if persist_state['minute_bucket'] is None:
                persist_state['minute_bucket'] = bucket
            elif bucket != persist_state['minute_bucket']:
                prev_bucket = persist_state['minute_bucket']
                prev_entry = persist_state['minute_entry']
                prev_exit = persist_state['minute_exit']
                if prev_entry > 0 or prev_exit > 0:
                    _save_traffic_flow_stat(
                        ts=prev_bucket,
                        entry=prev_entry,
                        exit_v=prev_exit,
                        total=prev_entry + prev_exit
                    )
                persist_state['minute_bucket'] = bucket
                persist_state['minute_entry'] = 0
                persist_state['minute_exit'] = 0
            persist_state['minute_entry'] += entry
            persist_state['minute_exit'] += exit_v
        elif PERSIST_MODE == 'video_end':
            persist_state['session_entry'] += entry
            persist_state['session_exit'] += exit_v

    return {
        'timestamp': ts,
        'entryCount': entry,
        'exitCount': exit_v,
        'totalCount': entry + exit_v,
        'todayCount': today_count,
        'currentHourCount': current_hour_count
    }


def get_traffic_stats_snapshot():
    with stats_lock:
        return {
            'today_count': traffic_stats['today_count'],
            'current_hour_count': traffic_stats['current_hour_count'],
            'entry_count': traffic_stats['entry_count'],
            'exit_count': traffic_stats['exit_count'],
            'last_timestamp': traffic_stats['last_timestamp']
        }


try:
    _init_traffic_flow_table()
except Exception as e:
    print(f"Warning: failed to init traffic_flow_stat table: {e}")


def register_socketio_events(socketio):
    """Register socket.io events."""
    global socketio_instance
    socketio_instance = socketio

    @socketio.on('connect', namespace='/stream/traffic')
    def handle_traffic_connect():
        print('Client connected to traffic stream')
        emit('connected', {'message': 'Connected to traffic stream'})

    @socketio.on('disconnect', namespace='/stream/traffic')
    def handle_traffic_disconnect():
        print('Client disconnected from traffic stream')

    @socketio.on('connect', namespace='/stream/detection')
    def handle_detection_connect():
        print('Client connected to detection stream')
        emit('connected', {'message': 'Connected to detection stream'})

    @socketio.on('disconnect', namespace='/stream/detection')
    def handle_detection_disconnect():
        print('Client disconnected from detection stream')

    @socketio.on('connect', namespace='/stream/video')
    def handle_video_connect():
        print('Client connected to video stream')
        emit('connected', {'message': 'Connected to video stream'})

    @socketio.on('disconnect', namespace='/stream/video')
    def handle_video_disconnect():
        print('Client disconnected from video stream')


def send_traffic_data(data):
    """Push traffic payload to /stream/traffic."""
    if socketio_instance:
        socketio_instance.emit('traffic_data', data, namespace='/stream/traffic')


def send_detection_data(data):
    """Push detection payload to /stream/detection."""
    if socketio_instance:
        socketio_instance.emit('detection_data', data, namespace='/stream/detection')


def send_video_frame(frame_data):
    """Push video frame payload to /stream/video."""
    if socketio_instance:
        socketio_instance.emit('video_frame', frame_data, namespace='/stream/video')


@streaming_bp.route('/traffic/stats', methods=['GET'])
def get_traffic_stats():
    """Return current traffic stats snapshot."""
    stats = get_traffic_stats_snapshot()
    return jsonify({
        'code': 200,
        'data': {
            # snake_case (compatibility)
            'today_count': stats['today_count'],
            'current_hour_count': stats['current_hour_count'],
            'entry_count': stats['entry_count'],
            'exit_count': stats['exit_count'],
            # camelCase (frontend convenience)
            'todayCount': stats['today_count'],
            'currentHourCount': stats['current_hour_count'],
            'entryCount': stats['entry_count'],
            'exitCount': stats['exit_count'],
            'timestamp': stats['last_timestamp']
        }
    })


@streaming_bp.route('/streaming/start', methods=['POST'])
def start_streaming():
    """Start Spark Streaming job."""
    global streaming_processor, streaming_thread

    if not SPARK_AVAILABLE:
        return jsonify({'code': 500, 'message': 'Spark Streaming unavailable. Install pyspark first.'})

    if streaming_processor is not None:
        return jsonify({'code': 400, 'message': 'Streaming already running'})

    try:
        streaming_processor = VehicleStreamingProcessor()

        def run_streaming():
            topics = [Config.KAFKA_TOPIC_VEHICLE, Config.KAFKA_TOPIC_TRAFFIC]
            streaming_processor.start_streaming(topics, streaming_processor.process_vehicle_stream)

        streaming_thread = threading.Thread(target=run_streaming, daemon=True)
        streaming_thread.start()

        return jsonify({'code': 200, 'message': 'Streaming started'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'Start failed: {str(e)}'})


@streaming_bp.route('/streaming/stop', methods=['POST'])
def stop_streaming():
    """Stop Spark Streaming job."""
    global streaming_processor

    if streaming_processor is None:
        return jsonify({'code': 400, 'message': 'Streaming is not running'})

    try:
        streaming_processor.stop()
        streaming_processor = None
        return jsonify({'code': 200, 'message': 'Streaming stopped'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'Stop failed: {str(e)}'})
