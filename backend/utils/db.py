# utils/db.py
import os, json, sqlite3
from contextlib import closing

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH  = os.path.join(DATA_DIR, "facemind.db")

def _connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with closing(_connect()) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            text TEXT NOT NULL,
            normalized TEXT NOT NULL,
            emotion TEXT NOT NULL,
            confidence REAL NOT NULL,
            latency_ms REAL NOT NULL,
            raw_scores TEXT
        );
        """)
        # indexes for faster metrics
        con.execute("CREATE INDEX IF NOT EXISTS idx_messages_emotion ON messages(emotion);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(ts);")

        # migrate: ensure raw_scores exists
        cols = [r["name"] for r in con.execute("PRAGMA table_info(messages)")]
        if "raw_scores" not in cols:
            con.execute("ALTER TABLE messages ADD COLUMN raw_scores TEXT;")

def log_message(text, normalized, emotion, confidence, latency_ms, raw_scores=None):
    """Insert one row. raw_scores is a dict (label->score) or None."""
    raw_json = None
    if isinstance(raw_scores, dict):
        raw_json = json.dumps(raw_scores, ensure_ascii=False)
    with closing(_connect()) as con:
        con.execute(
            "INSERT INTO messages (text, normalized, emotion, confidence, latency_ms, raw_scores)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (text, normalized, emotion, float(confidence), float(latency_ms), raw_json)
        )

def get_metrics():
    """Return simple aggregate metrics for dashboard/report."""
    with closing(_connect()) as con:
        # totals
        total, = con.execute("SELECT COUNT(*) FROM messages").fetchone()
        avg_latency, = con.execute("SELECT COALESCE(AVG(latency_ms), 0) FROM messages").fetchone()

        # counts by emotion
        rows = con.execute("""
            SELECT emotion, COUNT(*) as c,
                   ROUND(AVG(confidence), 3) AS avg_conf,
                   ROUND(AVG(latency_ms), 1) AS avg_latency
            FROM messages
            GROUP BY emotion
            ORDER BY c DESC
        """).fetchall()
        counts = {r["emotion"]: r["c"] for r in rows}
        per_emotion = [
            dict(emotion=r["emotion"], count=r["c"], avg_conf=r["avg_conf"], avg_latency=r["avg_latency"])
            for r in rows
        ]

        # last 7 days trend (optional, fine if table is empty)
        trend = con.execute("""
            SELECT DATE(ts) as day, COUNT(*) as c
            FROM messages
            WHERE ts >= DATE('now', '-7 day')
            GROUP BY DATE(ts)
            ORDER BY day ASC
        """).fetchall()
        daily = [dict(day=r["day"], count=r["c"]) for r in trend]

    return {
        "total": total,
        "avg_latency_ms": round(float(avg_latency or 0), 1),
        "counts": counts,
        "per_emotion": per_emotion,
        "last_7_days": daily,
    }
