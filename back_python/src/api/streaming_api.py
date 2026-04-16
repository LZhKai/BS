"""
SocketIO bridge used by video/detection features.

Spark micro-batch aggregation is handled by monitor_streaming.MonitorSparkStreamer;
aggregated metrics are pushed via send_monitor_agg_data().
"""
from flask_socketio import emit

socketio_instance = None


def register_socketio_events(socketio):
    """Register socket.io events."""
    global socketio_instance
    socketio_instance = socketio

    @socketio.on('connect', namespace='/stream/monitor')
    def handle_detection_connect():
        print('Client connected to detection stream')
        emit('connected', {'message': 'Connected to detection stream'})

    @socketio.on('disconnect', namespace='/stream/monitor')
    def handle_detection_disconnect():
        print('Client disconnected from detection stream')

    @socketio.on('connect', namespace='/stream/monitor-video')
    def handle_video_connect():
        print('Client connected to video stream')
        emit('connected', {'message': 'Connected to video stream'})

    @socketio.on('disconnect', namespace='/stream/monitor-video')
    def handle_video_disconnect():
        print('Client disconnected from video stream')


def send_detection_data(data):
    """Push detection payload to /stream/detection."""
    if socketio_instance:
        socketio_instance.emit('detection_data', data, namespace='/stream/monitor')


def send_monitor_agg_data(data):
    """Push micro-batch aggregate payload to /stream/monitor."""
    if socketio_instance:
        socketio_instance.emit('monitor_agg_data', data, namespace='/stream/monitor')


def send_video_frame(frame_data):
    """Push video frame payload to /stream/video."""
    if socketio_instance:
        socketio_instance.emit('video_frame', frame_data, namespace='/stream/monitor-video')
