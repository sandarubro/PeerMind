# backend/tools/export_csv.py
import os, csv, sqlite3, argparse, json
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE, "data", "facemind.db")

def export_csv(out_path, date_from=None, date_to=None):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    sql = "SELECT id, ts, text, normalized, emotion, confidence, latency_ms, raw_scores FROM messages"
    args = []
    if date_from and date_to:
        sql += " WHERE ts BETWEEN ? AND ?"
        args += [date_from, date_to]
    elif date_from:
        sql += " WHERE ts >= ?"
        args += [date_from]
    elif date_to:
        sql += " WHERE ts <= ?"
        args += [date_to]
    sql += " ORDER BY id ASC"

    rows = cur.execute(sql, args).fetchall()
    con.close()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","ts","text","normalized","emotion","confidence","latency_ms","raw_scores_json"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7] or ""])

    print(f"Exported {len(rows)} rows -> {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(BASE, "tools", "messages_export.csv"))
    ap.add_argument("--from", dest="date_from", default=None, help="YYYY-MM-DD HH:MM:SS or YYYY-MM-DD")
    ap.add_argument("--to",   dest="date_to",   default=None, help="YYYY-MM-DD HH:MM:SS or YYYY-MM-DD")
    args = ap.parse_args()

    export_csv(args.out, args.date_from, args.date_to)
