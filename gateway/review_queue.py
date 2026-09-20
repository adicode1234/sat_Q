"""SQLite persistence and analyst review workflow for change detection candidates.
Enforces the strict rule: No candidate is ever auto-confirmed or auto-hidden.
Ground truth is strictly established by human analyst confirmation.
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "review_queue.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS change_review_candidates (
                candidate_id TEXT PRIMARY KEY,
                analysis_id TEXT,
                created_at TEXT,
                query TEXT,
                status TEXT,
                decision TEXT DEFAULT 'pending',
                analyst_notes TEXT,
                decided_at TEXT,
                cloud_fraction REAL,
                valid_fraction REAL,
                change_fraction REAL,
                gate_summary TEXT,
                provenance TEXT,
                preview_before TEXT,
                preview_after TEXT
            )
        """)
        conn.commit()


init_db()


def add_candidate(
    analysis_id: str,
    query: str,
    status: str,
    gate_summary: Dict[str, Any],
    change_fraction: float = 0.0,
    preview_before: Optional[str] = None,
    preview_after: Optional[str] = None,
) -> str:
    cand_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO change_review_candidates (
                candidate_id, analysis_id, created_at, query, status, decision,
                cloud_fraction, valid_fraction, change_fraction, gate_summary,
                provenance, preview_before, preview_after
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cand_id,
                analysis_id,
                now,
                query,
                status,
                float(gate_summary.get("max_cloud_cover", 0.0)),
                float(gate_summary.get("min_valid_pixels", 1.0)),
                float(change_fraction),
                json.dumps(gate_summary),
                json.dumps(gate_summary.get("provenance", {})),
                preview_before,
                preview_after,
            ),
        )
        conn.commit()
    return cand_id


def get_candidates(
    decision: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM change_review_candidates WHERE 1=1"
    params: List[Any] = []
    if decision:
        query += " AND decision = ?"
        params.append(decision)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["gate_summary"] = json.loads(d["gate_summary"])
            except Exception:
                pass
            try:
                d["provenance"] = json.loads(d["provenance"])
            except Exception:
                pass
            result.append(d)
        return result


def confirm_candidate(candidate_id: str, analyst_notes: Optional[str] = None) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cur = conn.execute(
            """
            UPDATE change_review_candidates
            SET decision = 'confirmed', analyst_notes = ?, decided_at = ?
            WHERE candidate_id = ?
            """,
            (analyst_notes, now, candidate_id),
        )
        conn.commit()
        return cur.rowcount > 0


def reject_candidate(candidate_id: str, analyst_notes: Optional[str] = None) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cur = conn.execute(
            """
            UPDATE change_review_candidates
            SET decision = 'rejected', analyst_notes = ?, decided_at = ?
            WHERE candidate_id = ?
            """,
            (analyst_notes, now, candidate_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_stats() -> Dict[str, int]:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM change_review_candidates").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM change_review_candidates WHERE decision='pending'").fetchone()[0]
        confirmed = conn.execute("SELECT COUNT(*) FROM change_review_candidates WHERE decision='confirmed'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM change_review_candidates WHERE decision='rejected'").fetchone()[0]
        return {
            "total": total,
            "pending": pending,
            "confirmed": confirmed,
            "rejected": rejected,
        }
