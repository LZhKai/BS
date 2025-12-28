"""
视频处理API
"""
from flask import Blueprint, jsonify, request
import json

# 可选导入：视频处理模块
try:
    from src.video.video_processor import VideoProcessor
    VIDEO_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入VideoProcessor: {e}")
    VIDEO_PROCESSOR_AVAILABLE = False
    VideoProcessor = None

# 可选导入：检测数据发送
try:
    from src.api.streaming_api import send_detection_data
    SEND_DETECTION_AVAILABLE = True
except ImportError:
    SEND_DETECTION_AVAILABLE = False
    def send_detection_data(data):
        pass

video_bp = Blueprint('video', __name__)

# 全局视频处理器
video_processor = None

def detection_callback(result):
    """车辆检测结果回调"""
    # 发送到WebSocket
    if SEND_DETECTION_AVAILABLE:
        send_detection_data(result)
    
    # TODO: 可以同时发送到Kafka
    # kafka_producer.send(Config.KAFKA_TOPIC_VEHICLE, json.dumps(result))

@video_bp.route('/video/start', methods=['POST'])
def start_video_processing():
    """启动视频处理"""
    global video_processor
    
    if not VIDEO_PROCESSOR_AVAILABLE:
        return jsonify({'code': 500, 'message': '视频处理功能不可用，请安装opencv-python: pip install opencv-python'})
    
    if video_processor is not None and video_processor.is_running:
        return jsonify({'code': 400, 'message': '视频处理已在运行'})
    
    try:
        data = request.get_json() or {}
        source = data.get('source', None)
        
        video_processor = VideoProcessor(callback=detection_callback)
        video_processor.start(source)
        
        return jsonify({
            'code': 200,
            'message': '视频处理已启动',
            'data': {
                'source': source or 'default',
                'status': 'running'
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'启动失败: {str(e)}'})

@video_bp.route('/video/stop', methods=['POST'])
def stop_video_processing():
    """停止视频处理"""
    global video_processor
    
    if video_processor is None or not video_processor.is_running:
        return jsonify({'code': 400, 'message': '视频处理未运行'})
    
    try:
        video_processor.stop()
        video_processor = None
        return jsonify({'code': 200, 'message': '视频处理已停止'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'停止失败: {str(e)}'})

@video_bp.route('/video/status', methods=['GET'])
def get_video_status():
    """获取视频处理状态"""
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
    """获取识别历史"""
    # TODO: 从数据库查询识别历史
    return jsonify({
        'code': 200,
        'data': {
            'total': 0,
            'records': []
        }
    })

