import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "instance" / "tests.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_records (
            test_id TEXT PRIMARY KEY,
            operator_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            location TEXT,
            image_filename TEXT NOT NULL,
            image_hash TEXT NOT NULL,
            ai_result TEXT,
            ai_confidence REAL,
            ai_explanation TEXT,
            quality_json TEXT,
            classification_json TEXT,
            verification_status TEXT DEFAULT 'PENDING',
            verified_by TEXT,
            verification_note TEXT,
            record_signature TEXT NOT NULL,
            alert_required INTEGER DEFAULT 0,
            analysis TEXT,
            capture_method TEXT DEFAULT 'FILE_UPLOAD',
            video_filename TEXT
        )
    """)
    # Backward-compatible migration for databases created before these columns existed
    existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(test_records)")}
    if "alert_required" not in existing_cols:
        conn.execute("ALTER TABLE test_records ADD COLUMN alert_required INTEGER DEFAULT 0")
    if "analysis" not in existing_cols:
        conn.execute("ALTER TABLE test_records ADD COLUMN analysis TEXT")
    if "capture_method" not in existing_cols:
        conn.execute("ALTER TABLE test_records ADD COLUMN capture_method TEXT DEFAULT 'FILE_UPLOAD'")
    if "video_filename" not in existing_cols:
        conn.execute("ALTER TABLE test_records ADD COLUMN video_filename TEXT")
    conn.commit()
    conn.close()


def insert_record(record: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO test_records
        (test_id, operator_id, timestamp, location, image_filename, image_hash,
         ai_result, ai_confidence, ai_explanation, quality_json, classification_json,
         verification_status, record_signature, alert_required, analysis, capture_method,
         video_filename)
        VALUES (:test_id, :operator_id, :timestamp, :location, :image_filename, :image_hash,
                :ai_result, :ai_confidence, :ai_explanation, :quality_json, :classification_json,
                'PENDING', :record_signature, :alert_required, :analysis, :capture_method,
                :video_filename)
    """, record)
    conn.commit()
    conn.close()


def update_verification(test_id: str, status: str, verified_by: str, note: str):
    conn = get_conn()
    conn.execute("""
        UPDATE test_records
        SET verification_status = ?, verified_by = ?, verification_note = ?
        WHERE test_id = ?
    """, (status, verified_by, note, test_id))
    conn.commit()
    conn.close()


def get_record(test_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM test_records WHERE test_id = ?", (test_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def search_records(query: str = "", result_filter: str = "", status_filter: str = ""):
    conn = get_conn()
    sql = "SELECT * FROM test_records WHERE 1=1"
    params = []
    if query:
        sql += " AND (test_id LIKE ? OR operator_id LIKE ? OR location LIKE ?)"
        like = f"%{query}%"
        params += [like, like, like]
    if result_filter:
        sql += " AND ai_result = ?"
        params.append(result_filter)
    if status_filter:
        sql += " AND verification_status = ?"
        params.append(status_filter)
    sql += " ORDER BY timestamp DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def dashboard_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) c FROM test_records").fetchone()["c"]
    positive = conn.execute("SELECT COUNT(*) c FROM test_records WHERE ai_result='POSITIVE'").fetchone()["c"]
    negative = conn.execute("SELECT COUNT(*) c FROM test_records WHERE ai_result='NEGATIVE'").fetchone()["c"]
    inconclusive = conn.execute("SELECT COUNT(*) c FROM test_records WHERE ai_result='INCONCLUSIVE'").fetchone()["c"]
    pending = conn.execute("SELECT COUNT(*) c FROM test_records WHERE verification_status='PENDING'").fetchone()["c"]
    alerts = conn.execute(
        "SELECT COUNT(*) c FROM test_records WHERE alert_required=1 AND verification_status='PENDING'"
    ).fetchone()["c"]
    conn.close()
    return {
        "total": total, "positive": positive, "negative": negative,
        "inconclusive": inconclusive, "pending": pending, "alerts": alerts,
    }
