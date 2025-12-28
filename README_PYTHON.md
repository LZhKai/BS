# Python后端模块 - 实时数据处理与车辆识别

## 项目概述

这是智能小区车辆管理系统的Python后端模块，负责实时数据处理、视频监控和车辆识别功能。

## 功能特性

### 1. Spark Streaming实时数据处理
- 从Kafka接收车辆识别数据流
- 实时统计车流量
- 处理车辆进出数据

### 2. 视频监控与车辆识别
- 使用OpenCV处理视频流
- 使用YOLO模型进行车辆检测
- 支持实时车辆识别

### 3. WebSocket实时数据推送
- 实时推送车流量数据到前端
- 实时推送车辆识别结果

## 快速开始

### 1. 环境要求

- Python 3.8+
- Java 8+ (Spark需要)
- Kafka (可选，用于流处理)
- MySQL 5.7+

### 2. 安装依赖

```bash
cd back_python
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# Flask配置
HOST=0.0.0.0
PORT=5000
DEBUG=True

# Kafka配置（可选）
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_VEHICLE=vehicle_detection
KAFKA_TOPIC_TRAFFIC=traffic_flow

# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=vehicle_management

# Spark配置
SPARK_MASTER=local[*]

# 视频处理配置
VIDEO_SOURCE=0  # 0为摄像头，也可以是视频文件路径
VIDEO_FPS=30
VIDEO_WIDTH=1280
VIDEO_HEIGHT=720

# YOLO模型配置
YOLO_MODEL_PATH=models/yolo/yolov8n.pt
YOLO_CONFIDENCE=0.5
```

### 4. 下载YOLO模型

首次运行会自动下载YOLO模型，或手动下载：

```bash
mkdir -p models/yolo
# YOLOv8模型会自动下载，或从 https://github.com/ultralytics/ultralytics 下载
```

### 5. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## API接口

### REST API

- `GET /` - 健康检查
- `GET /api/traffic/stats` - 获取车流量统计
- `POST /api/video/start` - 启动视频处理
- `POST /api/video/stop` - 停止视频处理
- `GET /api/video/status` - 获取视频处理状态
- `POST /api/streaming/start` - 启动Spark Streaming
- `POST /api/streaming/stop` - 停止Spark Streaming

### WebSocket接口

- `ws://localhost:5000/stream/traffic` - 车流量实时数据流
- `ws://localhost:5000/stream/detection` - 车辆识别实时数据流

## 项目结构

```
back_python/
├── app.py                      # Flask应用入口
├── config.py                    # 配置文件
├── requirements.txt            # Python依赖
├── .env                        # 环境变量配置（需创建）
├── src/
│   ├── streaming/              # Spark Streaming模块
│   │   ├── spark_streaming.py  # 流处理逻辑
│   ├── video/                   # 视频处理模块
│   │   ├── video_processor.py  # 视频处理器
│   │   ├── vehicle_detector.py # 车辆检测器
│   ├── api/                     # API接口
│   │   ├── streaming_api.py    # 流处理API
│   │   └── video_api.py         # 视频处理API
│   └── utils/                   # 工具类
│       └── database.py          # 数据库工具
└── models/                      # 模型文件目录
    └── yolo/                    # YOLO模型文件
```

## 使用说明

### 启动视频识别

1. 启动Python后端服务
2. 在前端页面点击"开始识别"按钮
3. 系统会自动打开摄像头（或使用配置的视频源）
4. 实时识别结果会通过WebSocket推送到前端

### 查看实时数据

1. 访问前端"车流量统计"页面
2. 点击"连接数据流"按钮
3. 实时数据会通过图表展示

## 注意事项

1. **YOLO模型**：首次运行会自动下载YOLO模型，需要网络连接
2. **摄像头权限**：确保系统有摄像头访问权限
3. **Kafka（可选）**：如果不需要Kafka流处理，可以注释相关代码
4. **性能优化**：视频处理会消耗较多资源，建议在性能较好的机器上运行

## 故障排查

### 1. 无法连接WebSocket

- 检查Python后端服务是否启动
- 检查端口5000是否被占用
- 检查防火墙设置

### 2. 视频识别不工作

- 检查摄像头是否可用
- 检查YOLO模型是否下载成功
- 查看控制台错误信息

### 3. Spark Streaming无法启动

- 检查Java环境是否正确安装
- 检查Kafka是否启动（如果使用）
- 检查Spark配置是否正确

## 后续开发

- [ ] 车牌识别功能集成
- [ ] 数据库持久化识别结果
- [ ] 告警功能
- [ ] 性能优化

