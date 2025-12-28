"""
实时数据流API
"""
from flask import Blueprint, jsonify
from flask_socketio import emit
from config import Config
import threading

# 可选导入：Spark Streaming
SPARK_AVAILABLE = False
VehicleStreamingProcessor = None

try:
    from src.streaming.spark_streaming import VehicleStreamingProcessor
    SPARK_AVAILABLE = True
except ImportError as e:
    # 忽略导入错误，Spark Streaming为可选功能
    pass
except Exception as e:
    # 其他错误也忽略
    print(f"警告: Spark Streaming模块加载失败: {e}")

streaming_bp = Blueprint('streaming', __name__)

# 全局变量存储SocketIO实例和流处理器
socketio_instance = None
streaming_processor = None
streaming_thread = None

def register_socketio_events(socketio):
    """注册SocketIO事件"""
    global socketio_instance
    socketio_instance = socketio
    
    @socketio.on('connect', namespace='/stream/traffic')
    def handle_traffic_connect():
        """客户端连接"""
        print('客户端已连接到车流量流')
        emit('connected', {'message': '已连接到车流量实时数据流'})
    
    @socketio.on('disconnect', namespace='/stream/traffic')
    def handle_traffic_disconnect():
        """客户端断开"""
        print('客户端已断开车流量流连接')
    
    @socketio.on('connect', namespace='/stream/detection')
    def handle_detection_connect():
        """客户端连接"""
        print('客户端已连接到车辆识别流')
        emit('connected', {'message': '已连接到车辆识别实时数据流'})
    
    @socketio.on('disconnect', namespace='/stream/detection')
    def handle_detection_disconnect():
        """客户端断开"""
        print('客户端已断开车辆识别流连接')

def send_traffic_data(data):
    """发送车流量数据到WebSocket"""
    if socketio_instance:
        socketio_instance.emit('traffic_data', data, namespace='/stream/traffic')

def send_detection_data(data):
    """发送车辆识别数据到WebSocket"""
    if socketio_instance:
        socketio_instance.emit('detection_data', data, namespace='/stream/detection')

@streaming_bp.route('/traffic/stats', methods=['GET'])
def get_traffic_stats():
    """获取车流量统计"""
    # TODO: 从数据库或缓存中获取统计数据
    return jsonify({
        'code': 200,
        'data': {
            'today_count': 0,
            'current_hour_count': 0,
            'entry_count': 0,
            'exit_count': 0
        }
    })

@streaming_bp.route('/streaming/start', methods=['POST'])
def start_streaming():
    """启动Spark Streaming"""
    global streaming_processor, streaming_thread
    
    if not SPARK_AVAILABLE:
        return jsonify({'code': 500, 'message': 'Spark Streaming功能不可用，请安装pyspark: pip install pyspark'})
    
    if streaming_processor is not None:
        return jsonify({'code': 400, 'message': '流处理已在运行'})
    
    try:
        streaming_processor = VehicleStreamingProcessor()
        
        # 在单独线程中启动流处理
        def run_streaming():
            topics = [Config.KAFKA_TOPIC_VEHICLE, Config.KAFKA_TOPIC_TRAFFIC]
            streaming_processor.start_streaming(
                topics,
                streaming_processor.process_vehicle_stream
            )
        
        streaming_thread = threading.Thread(target=run_streaming, daemon=True)
        streaming_thread.start()
        
        return jsonify({'code': 200, 'message': '流处理已启动'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'启动失败: {str(e)}'})

@streaming_bp.route('/streaming/stop', methods=['POST'])
def stop_streaming():
    """停止Spark Streaming"""
    global streaming_processor
    
    if streaming_processor is None:
        return jsonify({'code': 400, 'message': '流处理未运行'})
    
    try:
        streaming_processor.stop()
        streaming_processor = None
        return jsonify({'code': 200, 'message': '流处理已停止'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'停止失败: {str(e)}'})

