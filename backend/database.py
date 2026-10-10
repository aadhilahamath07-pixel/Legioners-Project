import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "inspections.db"
VALID_STATUSES = {"Pending", "In Progress", "Resolved"}


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                image_width INTEGER NOT NULL,
                image_height INTEGER NOT NULL,
                count INTEGER NOT NULL,
                detections_json TEXT NOT NULL,
                annotated_image TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                latitude REAL,
                longitude REAL,
                priority_score REAL,
                priority_level TEXT,
                priority_explanation TEXT,
                priority_factors_json TEXT
            )
        """)

        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(inspections)").fetchall()
        }
        migrations = {
            "status": "ALTER TABLE inspections ADD COLUMN status TEXT NOT NULL DEFAULT 'Pending'",
            "latitude": "ALTER TABLE inspections ADD COLUMN latitude REAL",
            "longitude": "ALTER TABLE inspections ADD COLUMN longitude REAL",
            "priority_score": "ALTER TABLE inspections ADD COLUMN priority_score REAL",
            "priority_level": "ALTER TABLE inspections ADD COLUMN priority_level TEXT",
            "priority_explanation": "ALTER TABLE inspections ADD COLUMN priority_explanation TEXT",
            "priority_factors_json": "ALTER TABLE inspections ADD COLUMN priority_factors_json TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                connection.execute(statement)


def _row_to_inspection(row):
    item = dict(row)
    item["detections"] = json.loads(item.pop("detections_json"))
    factors_json = item.pop("priority_factors_json", None)
    item["priority_factors"] = json.loads(factors_json) if factors_json else None
    item["status"] = item.get("status") or "Pending"
    return item


def save_inspection(result):
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO inspections (
                filename, created_at, image_width, image_height,
                count, detections_json, annotated_image, status, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
            """,
            (
                result["filename"],
                created_at,
                result["image_width"],
                result["image_height"],
                result["count"],
                json.dumps(result["detections"]),
                result["annotated_image"],
                result.get("latitude"),
                result.get("longitude"),
            ),
        )
        inspection_id = cursor.lastrowid

    return {
        "id": inspection_id,
        "filename": result["filename"],
        "created_at": created_at,
        "image_width": result["image_width"],
        "image_height": result["image_height"],
        "count": result["count"],
        "detections": result["detections"],
        "annotated_image": result["annotated_image"],
        "status": "Pending",
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "priority_score": None,
        "priority_level": None,
        "priority_explanation": None,
        "priority_factors": None,
    }


def get_inspections():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, filename, created_at, image_width, image_height,
                   count, detections_json, annotated_image, status, latitude, longitude,
                   priority_score, priority_level, priority_explanation, priority_factors_json
            FROM inspections
            ORDER BY
                CASE priority_level WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 WHEN 'Low' THEN 2 ELSE 3 END,
                priority_score DESC,
                id DESC
        """).fetchall()
    return [_row_to_inspection(row) for row in rows]


def update_inspection_status(inspection_id, status):
    if status not in VALID_STATUSES:
        raise ValueError("Invalid status")

    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE inspections SET status = ? WHERE id = ?",
            (status, inspection_id),
        )
        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            """
            SELECT id, filename, created_at, image_width, image_height, count,
                   detections_json, annotated_image, status, latitude, longitude,
                   priority_score, priority_level, priority_explanation, priority_factors_json
            FROM inspections WHERE id = ?
            """,
            (inspection_id,),
        ).fetchone()

    return _row_to_inspection(row) if row else None


def update_inspection_priority(inspection_id, priority_result, factors):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE inspections
            SET priority_score = ?, priority_level = ?, priority_explanation = ?,
                priority_factors_json = ?
            WHERE id = ?
            """,
            (
                priority_result["score"],
                priority_result["priority"],
                priority_result["explanation"],
                json.dumps(factors),
                inspection_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute(
            """
            SELECT id, filename, created_at, image_width, image_height, count,
                   detections_json, annotated_image, status, latitude, longitude,
                   priority_score, priority_level, priority_explanation, priority_factors_json
            FROM inspections WHERE id = ?
            """,
            (inspection_id,),
        ).fetchone()
    return _row_to_inspection(row) if row else None


initialize_database()
