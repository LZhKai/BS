"""
车辆检测器 - 使用YOLO模型
"""
import json
from datetime import datetime
from config import Config

# 可选导入：OpenCV
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("警告: opencv-python未安装")

# 可选导入：YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("警告: ultralytics未安装，YOLO模型将不可用")

class VehicleDetector:
    """车辆检测器"""
    
    def __init__(self):
        """初始化检测器"""
        if not YOLO_AVAILABLE:
            print("警告: YOLO不可用，车辆检测功能将受限")
            self.model = None
        else:
            try:
                self.model = YOLO(Config.YOLO_MODEL_PATH)
                print(f"YOLO模型加载成功: {Config.YOLO_MODEL_PATH}")
            except Exception as e:
                print(f"YOLO模型加载失败: {e}")
                self.model = None
        
        # 车辆类别ID（COCO数据集中）
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        
    def detect_vehicles(self, frame):
        """检测视频帧中的车辆"""
        if self.model is None:
            return []
        
        # 使用YOLO进行检测
        results = self.model(frame, conf=Config.YOLO_CONFIDENCE, verbose=False)
        
        vehicles = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 检查是否是车辆类别
                cls = int(box.cls[0])
                if cls in self.vehicle_classes:
                    # 获取边界框坐标
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    
                    # 获取类别名称
                    class_name = result.names[cls]
                    
                    vehicles.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': confidence,
                        'class': class_name,
                        'class_id': cls
                    })
        
        return vehicles
    
    def draw_detections(self, frame, vehicles):
        """在帧上绘制检测结果"""
        if not CV2_AVAILABLE:
            return frame
        
        for vehicle in vehicles:
            x1, y1, x2, y2 = vehicle['bbox']
            confidence = vehicle['confidence']
            class_name = vehicle['class']
            
            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制标签
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame
    
    def format_detection_result(self, vehicles, frame_info=None):
        """格式化检测结果为JSON"""
        return {
            'timestamp': datetime.now().isoformat(),
            'vehicle_count': len(vehicles),
            'vehicles': vehicles,
            'frame_info': frame_info or {}
        }

