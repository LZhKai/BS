"""
视频处理器 - 处理视频流并进行车辆检测
"""
import os
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
    
    def __init__(self, callback=None, frame_callback=None):
        """
        初始化视频处理器
        :param callback: 检测结果回调函数
        :param frame_callback: 视频帧回调函数（用于发送到前端）
        """
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python未安装，无法使用视频处理功能。请安装: pip install opencv-python")
        
        if DETECTOR_AVAILABLE and VehicleDetector:
            self.detector = VehicleDetector()
        else:
            self.detector = None
            print("警告: VehicleDetector不可用，将跳过车辆检测")
        
        self.callback = callback
        self.frame_callback = frame_callback  # 视频帧回调（用于发送到前端）
        self.is_running = False
        self.cap = None
        self.thread = None
        self.current_vehicles = []  # 当前帧的检测结果
        
    def start(self, source=None):
        """启动视频处理"""
        if self.is_running:
            return
        
        source = source or Config.VIDEO_SOURCE
        
        # 处理视频文件路径
        if isinstance(source, str) and not source.isdigit():
            # 如果是相对路径（如 videos/test_video.mp4），转换为完整路径
            if not os.path.isabs(source):
                # 如果路径以 videos/ 开头，提取文件名
                if source.startswith('videos/') or source.startswith('videos\\'):
                    # videos/test_video.mp4 -> 提取 test_video.mp4
                    filename = source.replace('videos/', '').replace('videos\\', '')
                    source = os.path.join(Config.VIDEO_DIR, filename)
                else:
                    # 否则认为是 videos 目录下的文件
                    source = os.path.join(Config.VIDEO_DIR, source)
            # 检查文件是否存在
            if not os.path.exists(source):
                raise FileNotFoundError(f"视频文件不存在: {source}")
        else:
            # 尝试将source转换为整数（摄像头索引）
            try:
                if isinstance(source, str) and source.isdigit():
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
            vehicles = []
            
            # 每隔几帧检测一次（提高性能）
            if frame_count % 5 == 0 and self.detector:  # 每5帧检测一次
                # 进行车辆检测
                vehicles = self.detector.detect_vehicles(frame)
                self.current_vehicles = vehicles
                
                if vehicles:
                    # 格式化检测结果
                    result = self.detector.format_detection_result(vehicles, {
                        'frame_number': frame_count,
                        'fps': self.cap.get(cv2.CAP_PROP_FPS)
                    })
                    
                    # 调用回调函数
                    if self.callback:
                        self.callback(result)
            else:
                # 使用上一次的检测结果（保持检测框显示）
                vehicles = self.current_vehicles
            
            # 在帧上绘制检测框（用于显示）
            if self.detector and CV2_AVAILABLE:
                frame_with_boxes = self.detector.draw_detections(frame.copy(), vehicles)
            else:
                frame_with_boxes = frame
            
            # 发送视频帧到前端（每帧都发送）
            if self.frame_callback:
                self._send_frame(frame_with_boxes, vehicles, frame_count)
            
            # 控制帧率
            time.sleep(1.0 / Config.VIDEO_FPS)
    
    def _send_frame(self, frame, vehicles, frame_count):
        """发送视频帧到前端"""
        if not CV2_AVAILABLE:
            return
        
        try:
            import base64
            # 将帧编码为JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 发送帧数据
            frame_data = {
                'frame': frame_base64,
                'vehicles': vehicles,
                'frame_number': frame_count,
                'timestamp': time.time()
            }
            
            if self.frame_callback:
                self.frame_callback(frame_data)
        except Exception as e:
            print(f"发送视频帧失败: {e}")
    
    def get_frame(self):
        """获取当前帧（用于显示）"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

