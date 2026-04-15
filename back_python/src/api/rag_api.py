"""
RAG 智能问答相关 Flask API
"""
from flask import Blueprint, request, jsonify, Response
import json
from datetime import datetime

from src.rag.vehicle_rag_service import (
    rebuild_vehicle_vector_index,
    rag_search_vehicles,
)
from src.rag.embedding_service import encode_text
from src.rag.milvus_client import search_similar_vehicles
from src.rag.llm_service import stream_ask_about_vehicles
from src.utils.database import execute_insert, execute_query, execute_update

rag_bp = Blueprint("rag", __name__)

def _init_rag_log_table():
    execute_update(
        """
        CREATE TABLE IF NOT EXISTS rag_qa_log (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            answer LONGTEXT DEFAULT NULL,
            top_k INT NOT NULL DEFAULT 10,
            hit_count INT NOT NULL DEFAULT 0,
            hit_plates TEXT DEFAULT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
            error_message VARCHAR(255) DEFAULT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_create_time (create_time),
            KEY idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def _ensure_rag_log_columns():
    required_columns = {
        "top_k": "INT NOT NULL DEFAULT 10",
        "hit_count": "INT NOT NULL DEFAULT 0",
        "hit_plates": "TEXT DEFAULT NULL",
        "status": "VARCHAR(20) NOT NULL DEFAULT 'SUCCESS'",
        "error_message": "VARCHAR(255) DEFAULT NULL",
        "update_time": "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    }
    rows = execute_query(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'rag_qa_log'
        """
    )
    existing = set()
    for r in rows:
        col = getattr(r, "COLUMN_NAME", None)
        if col is None and len(r) > 0:
            col = r[0]
        if col:
            existing.add(str(col).lower())

    for col_name, col_ddl in required_columns.items():
        if col_name.lower() not in existing:
            execute_update(f"ALTER TABLE rag_qa_log ADD COLUMN {col_name} {col_ddl}")


def _save_rag_log(question: str, answer: str, top_k: int, vehicles, status: str = "SUCCESS", error_message: str = None):
    hit_plates = ",".join([str(v.get("plate_number", "")) for v in (vehicles or []) if v.get("plate_number")])
    execute_insert(
        """
        INSERT INTO rag_qa_log (question, answer, top_k, hit_count, hit_plates, status, error_message)
        VALUES (:question, :answer, :top_k, :hit_count, :hit_plates, :status, :error_message)
        """,
        {
            "question": question,
            "answer": answer,
            "top_k": int(top_k or 10),
            "hit_count": len(vehicles or []),
            "hit_plates": hit_plates or None,
            "status": status,
            "error_message": (error_message or None),
        },
    )


try:
    _init_rag_log_table()
    _ensure_rag_log_columns()
except Exception as e:
    print(f"Warning: failed to init rag_qa_log table: {e}")


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
    body: { "question": "白色的车有多少辆", "top_k": 10 }
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    top_k = int(data.get("top_k", 10))

    if not question:
        return jsonify({"code": 400, "message": "question 不能为空"}), 400

    try:
        result = rag_search_vehicles(question, top_k=top_k)
        _save_rag_log(
            question=question,
            answer=result.get("answer", ""),
            top_k=top_k,
            vehicles=result.get("vehicles", []),
            status="SUCCESS",
        )
        return jsonify({"code": 200, "message": "success", "data": result})
    except Exception as e:
        try:
            _save_rag_log(
                question=question,
                answer="",
                top_k=top_k,
                vehicles=[],
                status="FAILED",
                error_message=str(e)[:255],
            )
        except Exception:
            pass
        return jsonify({"code": 500, "message": f"RAG 查询失败: {e}"}), 500


@rag_bp.route("/rag/stream", methods=["GET"])
def api_rag_stream():
    """
    智能问答 / 向量检索接口（SSE 流式返回）
    GET /api/rag/stream?question=...&top_k=10

    事件：
    - event: meta  -> data: { "vehicles": [...] }
    - event: message (默认) -> data: { "token": "..." } 逐段回答
    - event: end   -> data: {}
    """
    question = (request.args.get("question") or "").strip()
    top_k = int(request.args.get("top_k", 10) or 10)

    if not question:
        return jsonify({"code": 400, "message": "question 不能为空"}), 400

    try:
        # 1) 编码问题并检索相似车辆
        query_emb = encode_text(question)
        vehicles = search_similar_vehicles(query_emb, top_k=top_k)

        def event_stream():
            answer_chunks = []
            # 先把检索到的车辆列表作为 meta 事件发送给前端
            meta = {"vehicles": vehicles}
            yield f"event: meta\ndata: {json.dumps(meta, ensure_ascii=False)}\n\n"

            # 再流式输出大模型回答
            try:
                for chunk in stream_ask_about_vehicles(question, vehicles):
                    if not chunk:
                        continue
                    answer_chunks.append(chunk)
                    payload = {"token": chunk}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

                full_answer = "".join(answer_chunks).strip()
                _save_rag_log(
                    question=question,
                    answer=full_answer,
                    top_k=top_k,
                    vehicles=vehicles,
                    status="SUCCESS",
                )
                # 结束事件
                yield "event: end\ndata: {}\n\n"
            except Exception as stream_error:
                partial_answer = "".join(answer_chunks).strip()
                try:
                    _save_rag_log(
                        question=question,
                        answer=partial_answer,
                        top_k=top_k,
                        vehicles=vehicles,
                        status="FAILED",
                        error_message=str(stream_error)[:255],
                    )
                except Exception:
                    pass
                err_payload = {"message": str(stream_error)}
                yield f"event: error\ndata: {json.dumps(err_payload, ensure_ascii=False)}\n\n"
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


@rag_bp.route("/rag/history", methods=["GET"])
def api_rag_history():
    current = int(request.args.get("current", 1))
    size = int(request.args.get("size", 10))
    offset = (current - 1) * size
    rows = execute_query(
        """
        SELECT id, question, answer, top_k, hit_count, hit_plates, status, error_message, create_time
        FROM rag_qa_log
        ORDER BY id DESC
        LIMIT :size OFFSET :offset
        """,
        {"size": size, "offset": offset},
    )
    total = execute_query("SELECT COUNT(1) AS cnt FROM rag_qa_log")[0].cnt

    records = []
    for r in rows:
        records.append(
            {
                "id": int(r.id),
                "question": r.question,
                "answer": r.answer,
                "topK": int(r.top_k or 0),
                "hitCount": int(r.hit_count or 0),
                "hitPlates": r.hit_plates or "",
                "status": r.status,
                "errorMessage": r.error_message,
                "createTime": r.create_time.strftime("%Y-%m-%d %H:%M:%S") if r.create_time else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return jsonify({"code": 200, "data": {"total": int(total), "records": records}})

