"""
视频处理器 - 处理视频流并进行车辆检测
"""
import threading
import time
import json
from config import Config

# 可选导入：OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("警告: opencv-python未安装，视频处理功能将不可用")

# 可选导入：车辆检测器
try:
    from src.video.vehicle_detector import VehicleDetector
    DETECTOR_AVAILABLE = True
except ImportError:
    DETECTOR_AVAILABLE = False
    VehicleDetector = None

class VideoProcessor:
    """视频处理器"""
    
    def __init__(self, callback=None):
        """
        初始化视频处理器
        :param callback: 检测结果回调函数
        """
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python未安装，无法使用视频处理功能。请安装: pip install opencv-python")
        
        if DETECTOR_AVAILABLE and VehicleDetector:
            self.detector = VehicleDetector()
        else:
            self.detector = None
            print("警告: VehicleDetector不可用，将跳过车辆检测")
        
        self.callback = callback
        self.is_running = False
        self.cap = None
        self.thread = None
        
    def start(self, source=None):
        """启动视频处理"""
        if self.is_running:
            return
        
        source = source or Config.VIDEO_SOURCE
        try:
            # 尝试将source转换为整数（摄像头索引）
            if source.isdigit():
                source = int(source)
        except:
            pass
        
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            raise Exception(f"无法打开视频源: {source}")
        
        # 设置视频参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.VIDEO_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.VIDEO_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, Config.VIDEO_FPS)
        
        self.is_running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        print(f"视频处理已启动，源: {source}")
    
    def stop(self):
        """停止视频处理"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        if self.thread:
            self.thread.join(timeout=2)
        print("视频处理已停止")
    
    def _process_loop(self):
        """处理循环"""
        frame_count = 0
        
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                print("无法读取视频帧")
                break
            
            frame_count += 1
            
            # 每隔几帧检测一次（提高性能）
            if frame_count % 5 == 0 and self.detector:  # 每5帧检测一次
                # 进行车辆检测
                vehicles = self.detector.detect_vehicles(frame)
                
                if vehicles:
                    # 格式化检测结果
                    result = self.detector.format_detection_result(vehicles, {
                        'frame_number': frame_count,
                        'fps': self.cap.get(cv2.CAP_PROP_FPS)
                    })
                    
                    # 调用回调函数
                    if self.callback:
                        self.callback(result)
            
            # 控制帧率
            time.sleep(1.0 / Config.VIDEO_FPS)
    
    def get_frame(self):
        """获取当前帧（用于显示）"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

