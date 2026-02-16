"""
初始化或重建车辆向量索引的脚本

可独立运行，也可作为 Flask 接口调用的实现。
"""
from .vehicle_rag_service import rebuild_vehicle_vector_index


def main():
    count = rebuild_vehicle_vector_index()
    print(f"已重建车辆向量索引，记录数：{count}")


if __name__ == "__main__":
    main()

