"""
配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置"""
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'vehicle-management-secret-key')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Kafka配置
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_VEHICLE = os.getenv('KAFKA_TOPIC_VEHICLE', 'vehicle_detection')
    KAFKA_TOPIC_TRAFFIC = os.getenv('KAFKA_TOPIC_TRAFFIC', 'traffic_flow')
    
    # MySQL配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '123456')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'vehicle_management')
    
    # Spark配置
    SPARK_MASTER = os.getenv('SPARK_MASTER', 'local[*]')
    SPARK_APP_NAME = 'VehicleManagementStreaming'
    
    # 视频处理配置
    VIDEO_SOURCE = os.getenv('VIDEO_SOURCE', 'videos/test_video.mp4')  # 视频文件路径，格式：videos/文件名.mp4，或使用摄像头：0
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
    VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1280))
    VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 720))
    
    # 视频文件目录（back_python/videos）
    _base_dir = os.path.dirname(os.path.abspath(__file__))  # back_python目录
    VIDEO_DIR = os.path.join(_base_dir, 'videos')
    
    @staticmethod
    def get_video_path(filename):
        """获取视频文件的完整路径"""
        return os.path.join(Config.VIDEO_DIR, filename)
    
    # YOLO模型配置
    YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'models/yolo/yolov8n.pt')
    YOLO_CONFIDENCE = float(os.getenv('YOLO_CONFIDENCE', 0.5))
    
    # 车牌识别配置（可选）
    PLATE_RECOGNITION_ENABLED = os.getenv('PLATE_RECOGNITION_ENABLED', 'False').lower() == 'true'
    
    @property
    def MYSQL_URL(self):
        """MySQL连接URL"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

