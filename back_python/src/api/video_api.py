"""
Video processing API.
"""
import os

from flask import Blueprint, jsonify, request
from config import Config

# Optional import: video processor
try:
    from src.video.video_processor import VideoProcessor
    VIDEO_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: failed to import VideoProcessor: {e}")
    VIDEO_PROCESSOR_AVAILABLE = False
    VideoProcessor = None

# Optional import: websocket senders and traffic stats updater
try:
    from src.api.streaming_api import (
        send_detection_data,
        send_traffic_data,
        update_traffic_stats,
        flush_traffic_persistence,
    )
    STREAMING_BRIDGE_AVAILABLE = True
except ImportError:
    STREAMING_BRIDGE_AVAILABLE = False

    def send_detection_data(_data):
        return None

    def send_traffic_data(_data):
        return None

    def update_traffic_stats(entry_count=0, exit_count=0, timestamp=None):
        return {
            'timestamp': timestamp,
            'entryCount': int(entry_count or 0),
            'exitCount': int(exit_count or 0),
            'totalCount': int(entry_count or 0) + int(exit_count or 0),
        }

    def flush_traffic_persistence(timestamp=None):
        return None


video_bp = Blueprint('video', __name__)

# Global processor instance
video_processor = None
TRACK_TTL_FRAMES = int(os.getenv('TRACK_TTL_FRAMES', '20'))
TRACK_IOU_THRESHOLD = 0.3
TRACK_CENTER_DIST_THRESHOLD = int(os.getenv('TRACK_CENTER_DIST_THRESHOLD', '100'))
TRACK_MIN_HITS = int(os.getenv('TRACK_MIN_HITS', '2'))
FLOW_LINE_Y = int(os.getenv('FLOW_LINE_Y', str(int(Config.VIDEO_HEIGHT * 0.5))))
FLOW_LINE_DEADZONE = int(os.getenv('FLOW_LINE_DEADZONE', '12'))
FLOW_ENTRY_DIRECTION = os.getenv('FLOW_ENTRY_DIRECTION', 'down').strip().lower()
FLOW_CROSS_COOLDOWN_FRAMES = int(os.getenv('FLOW_CROSS_COOLDOWN_FRAMES', '12'))
tracker_state = {
    'frame_index': 0,
    'next_track_id': 1,
    'tracks': [],
    'total_unique': 0,
    'total_by_type': {
        'car': 0,
        'truck': 0,
        'bus': 0,
        'motorcycle': 0
    }
}


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bbox_center_y(bbox):
    if not bbox or len(bbox) < 4:
        return None
    return (bbox[1] + bbox[3]) / 2.0


def _bbox_center_x(bbox):
    if not bbox or len(bbox) < 4:
        return None
    return (bbox[0] + bbox[2]) / 2.0


def _center_distance(box_a, box_b):
    ax = _bbox_center_x(box_a)
    ay = _bbox_center_y(box_a)
    bx = _bbox_center_x(box_b)
    by = _bbox_center_y(box_b)
    if ax is None or ay is None or bx is None or by is None:
        return float('inf')
    dx = ax - bx
    dy = ay - by
    return (dx * dx + dy * dy) ** 0.5


def _line_side(center_y):
    if center_y is None:
        return 0
    if center_y < (FLOW_LINE_Y - FLOW_LINE_DEADZONE):
        return -1
    if center_y > (FLOW_LINE_Y + FLOW_LINE_DEADZONE):
        return 1
    return 0


def _reset_tracker_state():
    tracker_state['frame_index'] = 0
    tracker_state['next_track_id'] = 1
    tracker_state['tracks'] = []
    tracker_state['total_unique'] = 0
    tracker_state['total_by_type'] = {
        'car': 0,
        'truck': 0,
        'bus': 0,
        'motorcycle': 0
    }


def _normalize_vehicle_type(class_name):
    name = (class_name or '').lower()
    if 'truck' in name:
        return 'truck'
    if 'bus' in name:
        return 'bus'
    if 'motorcycle' in name or 'motorbike' in name:
        return 'motorcycle'
    if 'car' in name:
        return 'car'
    return None


def _bbox_iou(box_a, box_b):
    if not box_a or not box_b or len(box_a) < 4 or len(box_b) < 4:
        return 0.0

    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    if inter_area <= 0:
        return 0.0

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union_area = area_a + area_b - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def _update_tracks(vehicles):
    tracker_state['frame_index'] += 1
    frame_index = tracker_state['frame_index']

    tracker_state['tracks'] = [
        track for track in tracker_state['tracks']
        if frame_index - track['last_seen'] <= TRACK_TTL_FRAMES
    ]

    matched_track_ids = set()
    new_by_type = {
        'car': 0,
        'truck': 0,
        'bus': 0,
        'motorcycle': 0
    }
    new_vehicle_count = 0
    entry_count = 0
    exit_count = 0

    for vehicle in vehicles:
        bbox = vehicle.get('bbox') or []
        vehicle_type = _normalize_vehicle_type(vehicle.get('class'))
        center_y = _bbox_center_y(bbox)
        current_side = _line_side(center_y)

        best_track = None
        best_iou = 0.0
        for track in tracker_state['tracks']:
            if track['track_id'] in matched_track_ids:
                continue

            iou = _bbox_iou(bbox, track['bbox'])
            center_dist = _center_distance(bbox, track['bbox'])
            if iou > best_iou or (best_track is None and center_dist <= TRACK_CENTER_DIST_THRESHOLD):
                best_iou = iou
                best_track = track

        if best_track and (best_iou >= TRACK_IOU_THRESHOLD or _center_distance(bbox, best_track['bbox']) <= TRACK_CENTER_DIST_THRESHOLD):
            prev_center_y = best_track.get('center_y')
            prev_side = best_track.get('line_side', 0)
            prev_cross_frame = best_track.get('last_cross_frame', -999999)
            already_counted = best_track.get('counted_crossing', False)

            best_track['bbox'] = bbox
            best_track['last_seen'] = frame_index
            best_track['hits'] += 1
            best_track['center_y'] = center_y
            best_track['line_side'] = current_side
            if not best_track.get('vehicle_type') and vehicle_type:
                best_track['vehicle_type'] = vehicle_type
            matched_track_ids.add(best_track['track_id'])
            vehicle['track_id'] = best_track['track_id']

            if (not best_track.get('unique_counted')) and best_track['hits'] >= TRACK_MIN_HITS:
                tracker_state['total_unique'] += 1
                new_vehicle_count += 1
                if best_track.get('vehicle_type') in tracker_state['total_by_type']:
                    tracker_state['total_by_type'][best_track['vehicle_type']] += 1
                    new_by_type[best_track['vehicle_type']] += 1
                best_track['unique_counted'] = True

            crossed_line = (prev_side in (-1, 1) and current_side in (-1, 1) and prev_side != current_side)
            cooldown_ok = (frame_index - prev_cross_frame) >= FLOW_CROSS_COOLDOWN_FRAMES
            if (not already_counted) and crossed_line and cooldown_ok and prev_center_y is not None and center_y is not None:
                moving_down = center_y > prev_center_y
                if FLOW_ENTRY_DIRECTION == 'up':
                    is_entry = not moving_down
                else:
                    is_entry = moving_down
                if is_entry:
                    entry_count += 1
                    vehicle['crossing'] = 'entry'
                else:
                    exit_count += 1
                    vehicle['crossing'] = 'exit'
                best_track['last_cross_frame'] = frame_index
                best_track['counted_crossing'] = True
            continue

        track_id = tracker_state['next_track_id']
        tracker_state['next_track_id'] += 1
        tracker_state['tracks'].append({
            'track_id': track_id,
            'bbox': bbox,
            'vehicle_type': vehicle_type,
            'last_seen': frame_index,
            'hits': 1,
            'center_y': center_y,
            'line_side': current_side,
            'last_cross_frame': -999999,
            'counted_crossing': False,
            'unique_counted': False
        })
        matched_track_ids.add(track_id)
        vehicle['track_id'] = track_id

        if TRACK_MIN_HITS <= 1:
            tracker_state['total_unique'] += 1
            new_vehicle_count += 1
            if vehicle_type in tracker_state['total_by_type']:
                tracker_state['total_by_type'][vehicle_type] += 1
                new_by_type[vehicle_type] += 1
            tracker_state['tracks'][-1]['unique_counted'] = True

    return {
        'new_vehicle_count': new_vehicle_count,
        'new_by_type': new_by_type,
        'unique_vehicle_count': tracker_state['total_unique'],
        'unique_by_type': dict(tracker_state['total_by_type']),
        'entry_count': entry_count,
        'exit_count': exit_count
    }


def detection_callback(result):
    """Handle vehicle detection callback from video pipeline."""
    vehicles = result.get('vehicles') or []
    tracking = _update_tracks(vehicles)
    frame_vehicle_count = _to_int(result.get('vehicle_count', len(vehicles)))
    if frame_vehicle_count <= 0:
        frame_vehicle_count = len(vehicles)

    result['vehicles'] = vehicles
    result['frame_vehicle_count'] = frame_vehicle_count
    result['vehicle_count'] = frame_vehicle_count
    result['new_vehicle_count'] = tracking['new_vehicle_count']
    result['new_by_type'] = tracking['new_by_type']
    result['unique_vehicle_count'] = tracking['unique_vehicle_count']
    result['unique_by_type'] = tracking['unique_by_type']
    result['entryCount'] = tracking['entry_count']
    result['exitCount'] = tracking['exit_count']
    result['lineY'] = FLOW_LINE_Y

    # Build traffic payload for the Traffic page.
    entry_count = result.get('entryCount', result.get('entry_count'))
    exit_count = result.get('exitCount', result.get('exit_count'))

    # Fallback when no crossing event is detected in this frame.
    # Keep traffic stats aligned with detection growth by counting new unique
    # vehicles as entry when entry/exit are both empty or zero.
    if entry_count is None and exit_count is None:
        entry_count = _to_int(result.get('new_vehicle_count', 0))
        exit_count = 0
    else:
        entry_count = _to_int(entry_count, 0)
        exit_count = _to_int(exit_count, 0)
        if entry_count == 0 and exit_count == 0:
            entry_count = _to_int(result.get('new_vehicle_count', 0))

    traffic_payload = update_traffic_stats(
        entry_count=_to_int(entry_count, 0),
        exit_count=_to_int(exit_count, 0),
        timestamp=result.get('timestamp')
    )

    # Align detection stream metrics with traffic metric fields.
    result['entryCount'] = traffic_payload.get('entryCount', 0)
    result['exitCount'] = traffic_payload.get('exitCount', 0)
    result['totalCount'] = traffic_payload.get('totalCount', 0)
    result['todayCount'] = traffic_payload.get('todayCount', result.get('todayCount', 0))
    result['currentHourCount'] = traffic_payload.get('currentHourCount', result.get('currentHourCount', 0))

    # Forward detection payload for the Detection page.
    if STREAMING_BRIDGE_AVAILABLE:
        send_detection_data(result)

    if STREAMING_BRIDGE_AVAILABLE:
        send_traffic_data(traffic_payload)



def frame_callback(frame_data):
    """Handle frame callback and forward to websocket."""
    try:
        from src.api.streaming_api import send_video_frame
        send_video_frame(frame_data)
    except Exception as e:
        print(f"Failed to send video frame: {e}")


def on_video_end(_reason='eof'):
    """Flush aggregated traffic stats when video naturally ends."""
    try:
        flush_traffic_persistence()
    except Exception as e:
        print(f"Failed to flush traffic stats on video end: {e}")


@video_bp.route('/video/start', methods=['POST'])
def start_video_processing():
    """Start video processing."""
    global video_processor

    if not VIDEO_PROCESSOR_AVAILABLE:
        return jsonify({'code': 500, 'message': 'Video processing unavailable. Install opencv-python first.'})

    if video_processor is not None and video_processor.is_running:
        return jsonify({'code': 400, 'message': 'Video processing already running'})

    try:
        _reset_tracker_state()
        data = request.get_json() or {}
        source = data.get('source', None)

        video_processor = VideoProcessor(
            callback=detection_callback,
            frame_callback=frame_callback,
            end_callback=on_video_end
        )
        video_processor.start(source)

        return jsonify({
            'code': 200,
            'message': 'Video processing started',
            'data': {
                'source': source or 'default',
                'status': 'running'
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'Start failed: {str(e)}'})


@video_bp.route('/video/stop', methods=['POST'])
def stop_video_processing():
    """Stop video processing."""
    global video_processor

    if video_processor is None or not video_processor.is_running:
        return jsonify({'code': 400, 'message': 'Video processing is not running'})

    try:
        video_processor.stop()
        flush_traffic_persistence()
        video_processor = None
        return jsonify({'code': 200, 'message': 'Video processing stopped'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'Stop failed: {str(e)}'})


@video_bp.route('/video/status', methods=['GET'])
def get_video_status():
    """Return video processing status."""
    global video_processor

    if video_processor is None:
        return jsonify({
            'code': 200,
            'data': {
                'status': 'stopped',
                'is_running': False
            }
        })

    return jsonify({
        'code': 200,
        'data': {
            'status': 'running' if video_processor.is_running else 'stopped',
            'is_running': video_processor.is_running
        }
    })


@video_bp.route('/detection/history', methods=['GET'])
def get_detection_history():
    """Return detection history (placeholder)."""
    return jsonify({
        'code': 200,
        'data': {
            'total': 0,
            'records': []
        }
    })
