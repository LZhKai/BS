"""
Video processor: read video stream, run vehicle detection, and push frames/results.
"""
import os
import threading
import time

from config import Config

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python is not installed.")

try:
    from src.video.vehicle_detector import VehicleDetector
    DETECTOR_AVAILABLE = True
except ImportError:
    DETECTOR_AVAILABLE = False
    VehicleDetector = None


class VideoProcessor:
    """Video processing worker."""

    def __init__(self, callback=None, frame_callback=None, end_callback=None):
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python is required: pip install opencv-python")

        if DETECTOR_AVAILABLE and VehicleDetector:
            self.detector = VehicleDetector()
        else:
            self.detector = None
            print("Warning: VehicleDetector unavailable, detection will be skipped.")

        self.callback = callback
        self.frame_callback = frame_callback
        self.end_callback = end_callback
        self.is_running = False
        self.cap = None
        self.thread = None
        self.current_vehicles = []

    def start(self, source=None):
        """Start video processing thread."""
        if self.is_running:
            return

        source = source or Config.VIDEO_SOURCE

        if isinstance(source, str) and not source.isdigit():
            if not os.path.isabs(source):
                if source.startswith('videos/') or source.startswith('videos\\'):
                    filename = source.replace('videos/', '').replace('videos\\', '')
                    source = os.path.join(Config.VIDEO_DIR, filename)
                else:
                    source = os.path.join(Config.VIDEO_DIR, source)
            if not os.path.exists(source):
                raise FileNotFoundError(f"Video file not found: {source}")
        else:
            try:
                if isinstance(source, str) and source.isdigit():
                    source = int(source)
            except Exception:
                pass

        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise Exception(f"Cannot open video source: {source}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.VIDEO_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.VIDEO_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, Config.VIDEO_FPS)

        self.is_running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        print(f"Video processing started, source: {source}")

    def stop(self):
        """Stop video processing thread."""
        self.is_running = False
        if self.cap:
            self.cap.release()
        if self.thread:
            self.thread.join(timeout=2)
        print("Video processing stopped")

    def _process_loop(self):
        """Main processing loop."""
        frame_count = 0
        finished_by_eof = False

        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    finished_by_eof = True
                    print("Video ended or frame read failed.")
                    break

                frame_count += 1
                vehicles = []

                if frame_count % 5 == 0 and self.detector:
                    vehicles = self.detector.detect_vehicles(frame)
                    self.current_vehicles = vehicles

                    if vehicles and self.callback:
                        result = self.detector.format_detection_result(
                            vehicles,
                            {
                                'frame_number': frame_count,
                                'fps': self.cap.get(cv2.CAP_PROP_FPS)
                            }
                        )
                        try:
                            self.callback(result)
                        except Exception as e:
                            print(f"Detection callback error: {e}")
                else:
                    vehicles = self.current_vehicles

                if self.detector and CV2_AVAILABLE:
                    frame_with_boxes = self.detector.draw_detections(frame.copy(), vehicles)
                else:
                    frame_with_boxes = frame

                if self.frame_callback:
                    self._send_frame(frame_with_boxes, vehicles, frame_count)

                time.sleep(1.0 / Config.VIDEO_FPS)
        finally:
            self.is_running = False
            if self.cap:
                self.cap.release()
            if finished_by_eof and self.end_callback:
                try:
                    self.end_callback('eof')
                except Exception as e:
                    print(f"end_callback failed: {e}")

    def _send_frame(self, frame, vehicles, frame_count):
        """Send encoded frame to callback."""
        if not CV2_AVAILABLE:
            return

        try:
            import base64

            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            frame_data = {
                'frame': frame_base64,
                'vehicles': vehicles,
                'frame_number': frame_count,
                'timestamp': time.time()
            }

            if self.frame_callback:
                self.frame_callback(frame_data)
        except Exception as e:
            print(f"Failed to send frame: {e}")

    def get_frame(self):
        """Get one frame from source."""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
