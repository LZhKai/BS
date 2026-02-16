"""
Plate recognition and vehicle persistence API.
"""
import os
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from config import Config
from src.utils.database import execute_insert, execute_query, execute_update
from src.video.plate_recognizer import PlateRecognizer

plate_bp = Blueprint("plate", __name__)
recognizer = PlateRecognizer()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _ensure_upload_dir():
    os.makedirs(Config.PLATE_UPLOAD_DIR, exist_ok=True)


def _init_record_table():
    execute_update(
        """
        CREATE TABLE IF NOT EXISTS plate_recognition_record (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            image_path VARCHAR(255) NOT NULL,
            recognized_plate VARCHAR(20) DEFAULT NULL,
            confidence DECIMAL(6,4) DEFAULT 0.0000,
            raw_text TEXT DEFAULT NULL,
            status VARCHAR(20) NOT NULL,
            error_message VARCHAR(255) DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_plate (recognized_plate),
            KEY idx_status (status),
            KEY idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def _save_record(image_path, recognized_plate, confidence, raw_text, status, error_message):
    row_id = execute_insert(
        """
        INSERT INTO plate_recognition_record
        (image_path, recognized_plate, confidence, raw_text, status, error_message)
        VALUES (:image_path, :recognized_plate, :confidence, :raw_text, :status, :error_message)
        """,
        {
            "image_path": image_path,
            "recognized_plate": recognized_plate,
            "confidence": confidence,
            "raw_text": raw_text,
            "status": status,
            "error_message": error_message,
        },
    )
    return int(row_id)


def _record_exists_plate(plate_number: str) -> bool:
    result = execute_query(
        "SELECT id FROM vehicle WHERE plate_number = :plate_number LIMIT 1",
        {"plate_number": plate_number},
    )
    return len(result) > 0


def _allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS


def _validate_plate_number(plate_number: str) -> bool:
    from src.video.plate_recognizer import PlateRecognizer

    for pattern in PlateRecognizer.PLATE_PATTERNS:
        if pattern.match(plate_number):
            return True
    for pattern in PlateRecognizer.RELAXED_PATTERNS:
        if pattern.match(plate_number):
            return True
    return False


_ensure_upload_dir()
try:
    _init_record_table()
except Exception as e:
    print(f"Warning: failed to init plate_recognition_record table: {e}")


@plate_bp.route("/plate/recognize", methods=["POST"])
def recognize_plate():
    if "file" not in request.files:
        return jsonify({"code": 400, "message": "Missing file field 'file'"})

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"code": 400, "message": "No file selected"})

    if not _allowed_file(file.filename):
        return jsonify({"code": 400, "message": "Unsupported file type"})

    file.seek(0, os.SEEK_END)
    size_bytes = file.tell()
    file.seek(0)
    if size_bytes > Config.MAX_UPLOAD_MB * 1024 * 1024:
        return jsonify({"code": 400, "message": f"File too large, max {Config.MAX_UPLOAD_MB}MB"})

    ext = os.path.splitext(file.filename)[1].lower()
    target_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    target_path = os.path.join(Config.PLATE_UPLOAD_DIR, target_name)
    file.save(target_path)

    try:
        result = recognizer.recognize(target_path)
        candidates = result.get("candidates", [])
        raw_text = ",".join([f"{c['plate_number']}:{c['confidence']:.3f}" for c in candidates])

        if result.get("success"):
            record_id = _save_record(
                image_path=target_name,
                recognized_plate=result["plate_number"],
                confidence=float(result["confidence"]),
                raw_text=raw_text,
                status="RECOGNIZED",
                error_message=None,
            )
            return jsonify(
                {
                    "code": 200,
                    "message": "识别成功",
                    "data": {
                        "recordId": record_id,
                        "plateNumber": result["plate_number"],
                        "confidence": float(result["confidence"]),
                        "candidates": candidates,
                    },
                }
            )

        record_id = _save_record(
            image_path=target_name,
            recognized_plate=None,
            confidence=0.0,
            raw_text=raw_text,
            status="FAILED",
            error_message=result.get("message", "No valid plate number detected"),
        )
        return jsonify(
            {
                "code": 400,
                "message": result.get("message", "识别失败"),
                "data": {"recordId": record_id, "candidates": candidates},
            }
        )
    except Exception as e:
        record_id = _save_record(
            image_path=target_name,
            recognized_plate=None,
            confidence=0.0,
            raw_text=None,
            status="FAILED",
            error_message=str(e)[:255],
        )
        return jsonify({"code": 500, "message": f"识别异常: {str(e)}", "data": {"recordId": record_id}})


@plate_bp.route("/plate/vehicle/save", methods=["POST"])
def save_vehicle_by_plate():
    data = request.get_json() or {}
    record_id = data.get("recordId")
    plate_number = (data.get("plateNumber") or "").strip().upper()
    owner_name = (data.get("ownerName") or "").strip()
    owner_phone = (data.get("ownerPhone") or "").strip()
    brand_model = (data.get("brandModel") or "").strip()
    description = (data.get("description") or "").strip()
    status = (data.get("status") or "NORMAL").strip()

    if not record_id:
        return jsonify({"code": 400, "message": "recordId is required"})
    if not plate_number:
        return jsonify({"code": 400, "message": "plateNumber is required"})
    if not owner_name:
        return jsonify({"code": 400, "message": "ownerName is required"})
    if not brand_model:
        return jsonify({"code": 400, "message": "brandModel is required"})
    if not _validate_plate_number(plate_number):
        return jsonify({"code": 400, "message": "车牌格式不合法"})

    try:
        if _record_exists_plate(plate_number):
            execute_update(
                "UPDATE plate_recognition_record SET status='DUPLICATE', error_message='Vehicle already exists' WHERE id=:id",
                {"id": record_id},
            )
            return jsonify({"code": 409, "message": "车牌已存在，未新增"})

        execute_update(
            """
            INSERT INTO vehicle
            (plate_number, owner_name, owner_phone, brand_model, description, status)
            VALUES (:plate_number, :owner_name, :owner_phone, :brand_model, :description, :status)
            """,
            {
                "plate_number": plate_number,
                "owner_name": owner_name,
                "owner_phone": owner_phone or None,
                "brand_model": brand_model,
                "description": description or None,
                "status": status or "NORMAL",
            },
        )

        execute_update(
            "UPDATE plate_recognition_record SET status='SAVED', recognized_plate=:plate WHERE id=:id",
            {"id": record_id, "plate": plate_number},
        )
        return jsonify({"code": 200, "message": "入库成功"})
    except Exception as e:
        execute_update(
            "UPDATE plate_recognition_record SET status='FAILED', error_message=:error_message WHERE id=:id",
            {"id": record_id, "error_message": str(e)[:255]},
        )
        return jsonify({"code": 500, "message": f"入库失败: {str(e)}"})


@plate_bp.route("/plate/records", methods=["GET"])
def list_plate_records():
    current = int(request.args.get("current", 1))
    size = int(request.args.get("size", 10))
    offset = (current - 1) * size

    rows = execute_query(
        """
        SELECT id, image_path, recognized_plate, confidence, status, error_message, created_at
        FROM plate_recognition_record
        ORDER BY id DESC
        LIMIT :size OFFSET :offset
        """,
        {"size": size, "offset": offset},
    )
    total = execute_query("SELECT COUNT(1) AS cnt FROM plate_recognition_record")[0].cnt

    records = [
        {
            "id": int(r.id),
            "imagePath": r.image_path,
            "recognizedPlate": r.recognized_plate,
            "confidence": float(r.confidence or 0),
            "status": r.status,
            "errorMessage": r.error_message,
            "createdAt": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
        }
        for r in rows
    ]

    return jsonify({"code": 200, "data": {"total": int(total), "records": records}})
