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
    
    # MySQL配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '123456')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'vehicle_management')
    
    # 视频处理配置
    VIDEO_SOURCE = os.getenv('VIDEO_SOURCE', 'videos/test_video.mp4')  # 视频文件路径，格式：videos/文件名.mp4，或使用摄像头：0
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
    VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1280))
    VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 720))
    MONITOR_STREAM_BATCH_SECONDS = int(os.getenv('MONITOR_STREAM_BATCH_SECONDS', 5))
    MONITOR_STREAM_WINDOW_SECONDS = int(os.getenv('MONITOR_STREAM_WINDOW_SECONDS', 30))
    
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
    PLATE_UPLOAD_DIR = os.getenv('PLATE_UPLOAD_DIR', os.path.join(_base_dir, 'uploads', 'plates'))
    MAX_UPLOAD_MB = int(os.getenv('MAX_UPLOAD_MB', 10))
    EASYOCR_LANGS = os.getenv('EASYOCR_LANGS', 'ch_sim,en')
    
    @property
    def MYSQL_URL(self):
        """MySQL连接URL"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    # --- RAG / 向量检索与大模型配置 ---
    # Milvus 向量数据库
    MILVUS_HOST = os.getenv('MILVUS_HOST', 'localhost')
    MILVUS_PORT = int(os.getenv('MILVUS_PORT', 19530))
    MILVUS_COLLECTION = os.getenv('MILVUS_COLLECTION', 'vehicle_info')

    # 嵌入模型
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')

    # 大模型 API（如 DeepSeek，经由 SiliconFlow 或兼容 OpenAI 接口）
    LLM_API_URL = os.getenv('LLM_API_URL', 'https://api.siliconflow.cn/v1/chat/completions')
    LLM_API_KEY = os.getenv('LLM_API_KEY', 'sk-judrfulsjhqnphriiqiisxxbkuojbautpilrpqnqcvpkwjcb')
    LLM_MODEL = os.getenv('LLM_MODEL', 'deepseek-ai/DeepSeek-V3')

