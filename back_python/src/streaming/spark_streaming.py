"""
Spark Streaming实时数据处理
"""
import json
from config import Config

# 可选导入：pyspark（需要Java环境）
PYSPARK_AVAILABLE = False

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import *
    from pyspark.sql.types import *
    from pyspark.streaming import StreamingContext
    from pyspark.streaming.kafka import KafkaUtils
    PYSPARK_AVAILABLE = True
except ImportError:
    # 静默处理，pyspark为可选依赖
    pass
except Exception as e:
    # 处理其他可能的错误（如pyspark已安装但有问题）
    print(f"警告: pyspark导入失败: {e}")

class VehicleStreamingProcessor:
    """车辆数据流处理器"""
    
    def __init__(self):
        if not PYSPARK_AVAILABLE:
            raise ImportError("pyspark未安装，无法使用Spark Streaming功能。请安装: pip install pyspark")
        
        self.spark = SparkSession.builder \
            .appName(Config.SPARK_APP_NAME) \
            .master(Config.SPARK_MASTER) \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        self.sc = self.spark.sparkContext
        self.ssc = StreamingContext(self.sc, batchDuration=5)  # 5秒一个批次
        
    def process_vehicle_stream(self, kafka_stream):
        """处理车辆识别数据流"""
        def parse_vehicle_data(rdd):
            """解析车辆数据"""
            try:
                data = json.loads(rdd)
                return {
                    'plate_number': data.get('plate_number', ''),
                    'detection_time': data.get('timestamp', ''),
                    'confidence': data.get('confidence', 0.0),
                    'location': data.get('location', ''),
                    'status': data.get('status', 'NORMAL')
                }
            except:
                return None
        
        # 解析JSON数据
        parsed_stream = kafka_stream.map(lambda x: parse_vehicle_data(x[1]))
        
        # 过滤无效数据
        valid_stream = parsed_stream.filter(lambda x: x is not None)
        
        # 统计每个时间窗口的车流量
        windowed_counts = valid_stream \
            .map(lambda x: (x['detection_time'][:16], 1)) \
            .reduceByKeyAndWindow(lambda x, y: x + y, lambda x, y: x - y, 60, 10)  # 60秒窗口，10秒滑动
        
        return windowed_counts
    
    def process_traffic_flow(self, kafka_stream):
        """处理车流量数据流"""
        def aggregate_traffic(rdd):
            """聚合车流量数据"""
            if rdd.isEmpty():
                return []
            
            # 按时间窗口统计
            traffic_data = rdd.map(lambda x: {
                'timestamp': x.get('timestamp', ''),
                'count': 1,
                'direction': x.get('direction', 'entry')  # entry/exit
            })
            
            # 统计进出车辆数
            entry_count = traffic_data.filter(lambda x: x['direction'] == 'entry').count()
            exit_count = traffic_data.filter(lambda x: x['direction'] == 'exit').count()
            
            return {
                'timestamp': traffic_data.first()['timestamp'] if traffic_data.count() > 0 else '',
                'entry_count': entry_count,
                'exit_count': exit_count,
                'total_count': entry_count + exit_count
            }
        
        return kafka_stream.map(lambda x: json.loads(x[1])).map(aggregate_traffic)
    
    def start_streaming(self, topics, process_func):
        """启动流处理"""
        kafka_params = {
            "bootstrap.servers": Config.KAFKA_BOOTSTRAP_SERVERS,
            "auto.offset.reset": "latest"
        }
        
        # 创建Kafka流
        kafka_stream = KafkaUtils.createDirectStream(
            self.ssc,
            topics,
            kafka_params
        )
        
        # 处理数据流
        processed_stream = process_func(kafka_stream)
        
        # 输出结果（可以发送到数据库或WebSocket）
        processed_stream.foreachRDD(self.save_results)
        
        # 启动流处理
        self.ssc.start()
        self.ssc.awaitTermination()
    
    def save_results(self, rdd):
        """保存处理结果"""
        # 这里可以将结果保存到数据库或通过WebSocket推送
        results = rdd.collect()
        for result in results:
            print(f"处理结果: {result}")
            # TODO: 保存到数据库或推送WebSocket
    
    def stop(self):
        """停止流处理"""
        self.ssc.stop(stopSparkContext=False, stopGraceFully=True)

