"""
Milvus 客户端与集合管理
"""
from typing import List, Dict, Any

from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
)

from config import Config


EMBEDDING_DIM = 384  # 与嵌入模型输出维度保持一致


def init_milvus_connection(alias: str = "default") -> None:
    """
    初始化 Milvus 连接
    """
    if not connections.has_connection(alias):
        connections.connect(
            alias=alias,
            host=Config.MILVUS_HOST,
            port=str(Config.MILVUS_PORT),
        )


def get_or_create_vehicle_collection() -> Collection:
    """
    获取或创建用于存储车辆向量的 Collection
    """
    init_milvus_connection()
    collection_name = Config.MILVUS_COLLECTION

    # 某些 Milvus / pymilvus 版本在 has_collection 时会直接抛出
    # “can't find collection” 异常，这里统一按“不存在”处理
    try:
        exists = utility.has_collection(collection_name)
    except Exception:
        exists = False

    if not exists:
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=False,
                description="车辆ID",
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=EMBEDDING_DIM,
                description="车辆信息向量",
            ),
            FieldSchema(name="plate_number", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="brand_model", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="owner_name", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="owner_phone", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="owner_address", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="status", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(
                name="text_content",
                dtype=DataType.VARCHAR,
                max_length=1024,
                description="用于检索和展示的完整文本",
            ),
        ]
        schema = CollectionSchema(fields=fields, description="车辆信息向量表")

        # 直接通过 Collection(name, schema=...) 创建新集合
        collection = Collection(name=collection_name, schema=schema)

        # 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 1024},
        }
        collection.create_index(field_name="embedding", index_params=index_params)
    else:
        collection = Collection(collection_name)

    return collection


def insert_vehicle_vectors(
    vectors: List[Dict[str, Any]],
) -> None:
    """
    批量插入车辆向量数据。

    每个向量字典需要包含：
    - id
    - embedding
    - plate_number
    - brand_model
    - description
    - owner_name
    - owner_phone
    - owner_address
    - status
    - text_content
    """
    if not vectors:
        return

    collection = get_or_create_vehicle_collection()

    ids = [v["id"] for v in vectors]
    embeddings = [v["embedding"] for v in vectors]
    # 将可能为 None 的字段统一转为空字符串，避免 Milvus 报 “expect string input, got NoneType”
    plate_numbers = [(v.get("plate_number") or "") for v in vectors]
    brand_models = [(v.get("brand_model") or "") for v in vectors]
    descriptions = [(v.get("description") or "") for v in vectors]
    owner_names = [(v.get("owner_name") or "") for v in vectors]
    owner_phones = [(v.get("owner_phone") or "") for v in vectors]
    owner_addresses = [(v.get("owner_address") or "") for v in vectors]
    statuses = [(v.get("status") or "") for v in vectors]
    text_contents = [(v.get("text_content") or "") for v in vectors]

    data = [
        ids,
        embeddings,
        plate_numbers,
        brand_models,
        descriptions,
        owner_names,
        owner_phones,
        owner_addresses,
        statuses,
        text_contents,
    ]

    collection.insert(data)
    collection.flush()


def search_similar_vehicles(
    query_embedding,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    根据查询向量在 Milvus 中检索相似车辆
    """
    collection = get_or_create_vehicle_collection()
    collection.load()

    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": 10},
    }

    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=[
            "id",
            "plate_number",
            "brand_model",
            "description",
            "owner_name",
            "owner_phone",
            "owner_address",
            "status",
            "text_content",
        ],
    )

    vehicles: List[Dict[str, Any]] = []
    if results:
        for hit in results[0]:
            entity = hit.entity
            vehicles.append(
                {
                    "id": entity.get("id"),
                    "plate_number": entity.get("plate_number"),
                    "brand_model": entity.get("brand_model"),
                    "description": entity.get("description"),
                    "owner_name": entity.get("owner_name"),
                    "owner_phone": entity.get("owner_phone"),
                    "owner_address": entity.get("owner_address"),
                    "status": entity.get("status"),
                    "text_content": entity.get("text_content"),
                    "distance": hit.distance,
                }
            )

    return vehicles


def clear_vehicle_collection() -> None:
    """
    清空车辆向量集合中的数据（用于重建索引）
    """
    init_milvus_connection()
    collection_name = Config.MILVUS_COLLECTION
    # 这里直接删除整个 collection，再由 get_or_create_vehicle_collection 重新创建，
    # 避免 “collection not loaded” 之类的问题
    try:
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
    except Exception:
        # 如果本来就不存在，忽略异常
        pass

