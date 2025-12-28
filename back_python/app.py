"""
Flask应用入口
"""
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from config import Config

# 可选导入：API蓝图
try:
    from src.api.streaming_api import streaming_bp
    STREAMING_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入streaming_api: {e}")
    STREAMING_AVAILABLE = False
    streaming_bp = None

try:
    from src.api.video_api import video_bp
    VIDEO_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入video_api: {e}")
    VIDEO_AVAILABLE = False
    video_bp = None

app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 初始化SocketIO（使用threading模式，更稳定）
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 注册蓝图（如果可用）
if STREAMING_AVAILABLE and streaming_bp:
    app.register_blueprint(streaming_bp, url_prefix='/api')
if VIDEO_AVAILABLE and video_bp:
    app.register_blueprint(video_bp, url_prefix='/api')

# 导入SocketIO事件处理（如果可用）
if STREAMING_AVAILABLE:
    try:
        from src.api.streaming_api import register_socketio_events
        register_socketio_events(socketio)
    except Exception as e:
        print(f"警告: 无法注册SocketIO事件: {e}")

@app.route('/')
def index():
    """健康检查"""
    return {
        'status': 'ok',
        'message': 'Vehicle Management Python Backend',
        'version': '1.0.0'
    }

if __name__ == '__main__':
    print(f"启动Python后端服务: http://{Config.HOST}:{Config.PORT}")
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

