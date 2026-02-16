"""
RAG 核心业务逻辑：
- 从 MySQL 读取车辆与车主信息，构建文本并向量化，写入 Milvus
- 基于自然语言问题检索相似车辆并调用 LLM 生成答案
"""
from typing import List, Dict, Any

from sqlalchemy import text

from src.utils.database import engine
from .embedding_service import encode_text, encode_texts
from .milvus_client import (
    insert_vehicle_vectors,
    search_similar_vehicles,
    clear_vehicle_collection,
)
from .llm_service import ask_about_vehicles


def _load_vehicle_owner_rows() -> List[Dict[str, Any]]:
    """
    从 MySQL 读取车辆与车主信息（左连接）
    """
    sql = text(
        """
        SELECT
            v.id AS id,
            v.plate_number AS plate_number,
            v.brand_model AS brand_model,
            v.description AS description,
            v.status AS status,
            v.owner_name AS owner_name,
            v.owner_phone AS owner_phone,
            o.address AS owner_address
        FROM vehicle v
        LEFT JOIN vehicle_owner o ON v.owner_id = o.id
        """
    )
    with engine.connect() as conn:
        result = conn.execute(sql)
        rows = []
        for r in result.mappings():
            rows.append(dict(r))
    return rows


def _build_text_for_row(row: Dict[str, Any]) -> str:
    """
    为单条车辆记录构建用于向量化的文本
    """
    parts = [
        f"车牌号: {row.get('plate_number','')}",
        f"品牌型号: {row.get('brand_model','')}",
        f"车辆描述: {row.get('description','')}",
        f"车主姓名: {row.get('owner_name','')}",
        f"车主电话: {row.get('owner_phone','')}",
        f"车主地址: {row.get('owner_address','')}",
        f"状态: {row.get('status','')}",
    ]
    return "；".join(p for p in parts if p)


def rebuild_vehicle_vector_index() -> int:
    """
    重建车辆向量索引：清空 Milvus 集合并重新插入所有车辆数据

    :return: 已索引车辆数量
    """
    rows = _load_vehicle_owner_rows()
    if not rows:
        clear_vehicle_collection()
        return 0

    # 构建文本
    texts = [_build_text_for_row(r) for r in rows]
    embeddings = encode_texts(texts)

    # 先清空集合
    clear_vehicle_collection()

    vectors: List[Dict[str, Any]] = []
    for row, emb, text_content in zip(rows, embeddings, texts):
        vectors.append(
            {
                "id": row["id"],
                "embedding": emb,
                "plate_number": row.get("plate_number", ""),
                "brand_model": row.get("brand_model", ""),
                "description": row.get("description", ""),
                "owner_name": row.get("owner_name", ""),
                "owner_phone": row.get("owner_phone", ""),
                "owner_address": row.get("owner_address", ""),
                "status": row.get("status", ""),
                "text_content": text_content,
            }
        )

    insert_vehicle_vectors(vectors)
    return len(vectors)


def rag_search_vehicles(question: str, top_k: int = 5) -> Dict[str, Any]:
    """
    主入口：根据用户问题进行向量检索并调用 LLM 生成回答
    """
    # 1) 将问题编码为向量
    query_emb = encode_text(question)

    # 2) 在 Milvus 中检索相似车辆
    vehicles = search_similar_vehicles(query_emb, top_k=top_k)

    # 3) 调用 LLM 生成自然语言答案
    answer = ask_about_vehicles(question, vehicles)

    return {
        "question": question,
        "answer": answer,
        "vehicles": vehicles,
    }

