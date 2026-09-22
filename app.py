import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, jsonify

import database
import pipeline
import security

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
database.init_db()


@app.context_processor
def inject_global_alerts():
    """Makes the pending-alert count available on every page (navbar), not
    just the dashboard, so an inconclusive result is visible immediately no
    matter where the officer navigates to next."""
    try:
        stats = database.dashboard_stats()
        return {"global_alerts_count": stats["alerts"]}
    except Exception:
        return {"global_alerts_count": 0}


def read_image_from_upload(file_storage) -> tuple:
    file_bytes = file_storage.read()
    np_arr = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image, file_bytes


@app.route("/")
def home():
    stats = database.dashboard_stats()
    return render_template("index.html", stats=stats)


@app.route("/new-test", methods=["GET", "POST"])
def new_test():
    if request.method == "GET":
        return render_template("new_test.html")

    operator_id = request.form.get("operator_id", "UNKNOWN")
    location = request.form.get("location", "")
    image_file = request.files.get("image")
    video_file = request.files.get("video")
    client_capture_timestamp = request.form.get("capture_timestamp", "").strip()

    if not image_file or image_file.filename == "":
        return render_template("new_test.html", error="Please choose a test image to upload.")

    image, raw_bytes = read_image_from_upload(image_file)
    if image is None:
        return render_template("new_test.html", error="Could not read that image file.")

    test_id = "T-" + uuid.uuid4().hex[:8].upper()
    image_filename = f"{test_id}.jpg"
    image_path = UPLOAD_DIR / image_filename
    with open(image_path, "wb") as f:
        f.write(raw_bytes)

    video_filename = None
    if video_file and video_file.filename:
        video_filename = f"{test_id}_reaction.webm"
        video_path = UPLOAD_DIR / video_filename
        video_file.save(video_path)

    image_hash = security.hash_image_bytes(raw_bytes)
    pipeline_result = pipeline.run_pipeline(image)

    ai_result = None
    ai_confidence = None
    ai_explanation = None
    alert_required = 0
    analysis = None
    if pipeline_result["stage_reached"] == "classification":
        cls = pipeline_result["classification"]
        ai_result = cls["result"]
        ai_confidence = cls["confidence"]
        ai_explanation = cls["explanation"]
        alert_required = 1 if cls.get("alert") else 0
        analysis = cls.get("analysis")

    timestamp = datetime.now(timezone.utc).isoformat()
    capture_method = "FILE_UPLOAD"
    if client_capture_timestamp:
        # This is the timestamp the browser recorded at the exact moment the
        # frame was grabbed from the live camera feed -- more accurate than
        # server-received time, which can lag behind by however long the
        # upload/network took.
        timestamp = client_capture_timestamp
        capture_method = "LIVE_CAPTURE"

    core_record = {
        "test_id": test_id,
        "operator_id": operator_id,
        "timestamp": timestamp,
        "location": location,
        "image_filename": image_filename,
        "image_hash": image_hash,
        "ai_result": ai_result,
        "ai_confidence": ai_confidence,
        "ai_explanation": ai_explanation,
        "capture_method": capture_method,
    }
    signature = security.sign_record(core_record)

    record = dict(core_record)
    record["quality_json"] = json.dumps(pipeline_result["quality"])
    record["classification_json"] = json.dumps(pipeline_result.get("classification"))
    record["record_signature"] = signature
    record["alert_required"] = alert_required
    record["analysis"] = analysis
    record["capture_method"] = capture_method
    record["video_filename"] = video_filename
    database.insert_record(record)

    return redirect(url_for("test_detail", test_id=test_id))


@app.route("/test/<test_id>")
def test_detail(test_id):
    record = database.get_record(test_id)
    if not record:
        return "Test not found", 404
    record["quality"] = json.loads(record["quality_json"]) if record["quality_json"] else None
    record["classification"] = json.loads(record["classification_json"]) if record["classification_json"] else None

    core_record = {
        "test_id": record["test_id"],
        "operator_id": record["operator_id"],
        "timestamp": record["timestamp"],
        "location": record["location"],
        "image_filename": record["image_filename"],
        "image_hash": record["image_hash"],
        "ai_result": record["ai_result"],
        "ai_confidence": record["ai_confidence"],
        "ai_explanation": record["ai_explanation"],
        "capture_method": record["capture_method"],
    }
    signature_valid = security.verify_record(core_record, record["record_signature"])

    return render_template("test_detail.html", record=record, signature_valid=signature_valid)


@app.route("/test/<test_id>/verify", methods=["POST"])
def verify_test(test_id):
    status = request.form.get("status")
    verified_by = request.form.get("verified_by", "UNKNOWN")
    note = request.form.get("note", "")
    database.update_verification(test_id, status, verified_by, note)
    return redirect(url_for("test_detail", test_id=test_id))


@app.route("/test/<test_id>/tamper-check", methods=["POST"])
def tamper_check(test_id):
    """Recompute the image hash from disk and compare to the stored hash --
    demonstrates the tampering-detection feature described in the brief."""
    record = database.get_record(test_id)
    if not record:
        return jsonify({"error": "not found"}), 404
    image_path = UPLOAD_DIR / record["image_filename"]
    with open(image_path, "rb") as f:
        current_hash = security.hash_image_bytes(f.read())
    matches = current_hash == record["image_hash"]
    return jsonify({
        "stored_hash": record["image_hash"],
        "current_hash": current_hash,
        "matches": matches,
    })


@app.route("/history")
def history():
    query = request.args.get("q", "")
    result_filter = request.args.get("result", "")
    status_filter = request.args.get("status", "")
    records = database.search_records(query, result_filter, status_filter)
    return render_template("history.html", records=records, query=query,
                            result_filter=result_filter, status_filter=status_filter)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
