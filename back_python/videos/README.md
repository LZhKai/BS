# 视频文件目录

此目录用于存放待处理的MP4视频文件。

## 使用方法

### 1. 放置视频文件

将MP4视频文件放在此目录下，例如：
```
videos/
  ├── test_video.mp4
  ├── traffic_001.mp4
  └── parking_lot.mp4
```

### 2. 通过API启动视频处理

**方式一：使用默认视频**
```bash
POST http://localhost:5000/api/video/start
Content-Type: application/json

{}
```

**方式二：指定视频文件（固定路径格式）**
```bash
POST http://localhost:5000/api/video/start
Content-Type: application/json

{
  "source": "/videos/test_video.mp4"
}
```

或者：
```json
{
  "source": "videos/test_video.mp4"
}
```

### 3. 前端访问视频（如果需要）

如果前端需要直接访问视频文件，可以通过：
```
http://localhost:5000/videos/test_video.mp4
```

## 注意事项

1. **文件格式**：目前支持MP4格式，其他格式可能需要转换
2. **文件大小**：建议视频文件不要过大，以免影响处理性能
3. **文件路径**：使用固定格式 `/videos/文件名.mp4` 或 `videos/文件名.mp4`
4. **摄像头**：使用摄像头时，传入 `"0"` 或 `0`（0为默认摄像头）

## 支持的视频源

- 摄像头：`"source": "0"` 或 `"source": 0`（0为默认摄像头）
- 视频文件：`"source": "videos/test_video.mp4"` 或绝对路径

