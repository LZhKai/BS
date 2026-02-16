"""
RAG 智能问答相关 Flask API
"""
from flask import Blueprint, request, jsonify, Response
import json

from src.rag.vehicle_rag_service import (
    rebuild_vehicle_vector_index,
    rag_search_vehicles,
)
from src.rag.embedding_service import encode_text
from src.rag.milvus_client import search_similar_vehicles
from src.rag.llm_service import stream_ask_about_vehicles

rag_bp = Blueprint("rag", __name__)


@rag_bp.route("/rag/index", methods=["POST"])
def api_rebuild_index():
    """
    重建车辆向量索引
    """
    count = rebuild_vehicle_vector_index()
    return jsonify({"code": 200, "message": "索引重建完成", "data": {"count": count}})


@rag_bp.route("/rag/search", methods=["POST"])
def api_rag_search():
    """
    智能问答 / 向量检索接口（一次性返回）
    body: { "question": "白色的车有多少辆", "top_k": 5 }
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    top_k = int(data.get("top_k", 5))

    if not question:
        return jsonify({"code": 400, "message": "question 不能为空"}), 400

    try:
        result = rag_search_vehicles(question, top_k=top_k)
        return jsonify({"code": 200, "message": "success", "data": result})
    except Exception as e:
        return jsonify({"code": 500, "message": f"RAG 查询失败: {e}"}), 500


@rag_bp.route("/rag/stream", methods=["GET"])
def api_rag_stream():
    """
    智能问答 / 向量检索接口（SSE 流式返回）
    GET /api/rag/stream?question=...&top_k=5

    事件：
    - event: meta  -> data: { "vehicles": [...] }
    - event: message (默认) -> data: { "token": "..." } 逐段回答
    - event: end   -> data: {}
    """
    question = (request.args.get("question") or "").strip()
    top_k = int(request.args.get("top_k", 5) or 5)

    if not question:
        return jsonify({"code": 400, "message": "question 不能为空"}), 400

    try:
        # 1) 编码问题并检索相似车辆
        query_emb = encode_text(question)
        vehicles = search_similar_vehicles(query_emb, top_k=top_k)

        def event_stream():
            # 先把检索到的车辆列表作为 meta 事件发送给前端
            meta = {"vehicles": vehicles}
            yield f"event: meta\ndata: {json.dumps(meta, ensure_ascii=False)}\n\n"

            # 再流式输出大模型回答
            for chunk in stream_ask_about_vehicles(question, vehicles):
                if not chunk:
                    continue
                payload = {"token": chunk}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            # 结束事件
            yield "event: end\ndata: {}\n\n"

        # 明确指定 UTF-8，避免中文在某些环境下出现乱码
        return Response(
            event_stream(),
            content_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        return jsonify({"code": 500, "message": f"RAG 流式查询失败: {e}"}), 500

