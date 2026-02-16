# Python后端 - 实时数据处理与车辆识别模块

## 项目简介

本模块负责智能小区车辆管理系统的实时数据处理、视频监控和车辆识别功能。

## 功能模块

1. **Spark Streaming实时数据处理**
   - 接收Kafka消息流
   - 实时统计车流量
   - 处理车辆识别结果

2. **视频监控与车辆识别**
   - 使用OpenCV处理视频流
   - 使用YOLO模型进行车辆检测
   - 车牌识别（可选）

3. **实时数据推送**
   - WebSocket实时推送车流量数据
   - 实时推送车辆识别结果

## 技术栈

- Flask：Web框架
- Flask-SocketIO：WebSocket支持
- PySpark：实时流处理
- Kafka：消息队列
- OpenCV：视频处理
- YOLO：车辆检测
- MySQL：数据存储

## 项目结构

```
back_python/
├── app.py                 # Flask应用入口
├── config.py              # 配置文件
├── requirements.txt       # Python依赖
├── src/
│   ├── streaming/         # Spark Streaming模块
│   │   ├── __init__.py
│   │   ├── spark_streaming.py
│   │   └── kafka_consumer.py
│   ├── video/              # 视频处理模块
│   │   ├── __init__.py
│   │   ├── video_processor.py
│   │   ├── vehicle_detector.py
│   │   └── plate_recognizer.py
│   ├── api/                # API接口
│   │   ├── __init__.py
│   │   ├── streaming_api.py
│   │   └── video_api.py
│   └── utils/              # 工具类
│       ├── __init__.py
│       └── database.py
└── models/                 # 模型文件目录
    └── yolo/               # YOLO模型文件
```

## 快速开始

### 1. 安装依赖

```bash
cd back_python
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_VEHICLE=vehicle_detection
KAFKA_TOPIC_TRAFFIC=traffic_flow

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=vehicle_management

SPARK_MASTER=local[*]
```

### 3. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## API接口

### WebSocket接口

- `ws://localhost:5000/stream/traffic` - 实时车流量数据流
- `ws://localhost:5000/stream/detection` - 实时车辆识别结果流

### REST API

- `GET /api/traffic/stats` - 获取车流量统计
- `POST /api/video/process` - 处理视频流
- `GET /api/detection/history` - 获取识别历史

### Plate Recognition APIs

- `POST /api/plate/recognize` - upload image (`file`) and recognize plate
- `POST /api/plate/vehicle/save` - confirm and save recognized vehicle into `vehicle`
- `GET /api/plate/records` - list recognition records (paged)

