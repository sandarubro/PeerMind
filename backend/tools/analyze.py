# backend/tools/analyze.py
import os, sqlite3, json, math
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE, "data", "facemind.db")
FIG_DIR = os.path.join(BASE, "..", "docs", "figures")

def fetch():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT emotion, confidence, latency_ms FROM messages")
    rows = cur.fetchall()
    con.close()
    return rows

def main():
    rows = fetch()
    if not rows:
        print("No data yet. Chat a bit first, then re-run.")
        return

    # Aggregate
    counts = {}
    sum_latency = {}
    sum_conf = {}
    for emo, conf, lat in rows:
        counts[emo] = counts.get(emo, 0) + 1
        sum_latency[emo] = sum_latency.get(emo, 0.0) + float(lat or 0)
        sum_conf[emo] = sum_conf.get(emo, 0.0) + float(conf or 0)

    avg_latency = {k: (sum_latency[k]/counts[k]) for k in counts}
    avg_conf    = {k: (sum_conf[k]/counts[k]) for k in counts}

    # Print summary for thesis appendix
    print("=== Summary ===")
    total = sum(counts.values())
    print(f"Total messages: {total}")
    for emo in sorted(counts, key=counts.get, reverse=True):
        print(f"{emo:>8}: {counts[emo]} msgs | avg_conf={avg_conf[emo]:.3f} | avg_latency={avg_latency[emo]:.1f} ms")

    # Charts dir
    os.makedirs(FIG_DIR, exist_ok=True)

    # Emotion counts chart
    emos = list(sorted(counts, key=counts.get, reverse=True))
    vals = [counts[e] for e in emos]
    plt.figure()
    plt.bar(emos, vals)
    plt.title("Message Count by Emotion")
    plt.xlabel("Emotion")
    plt.ylabel("Count")
    plt.tight_layout()
    out1 = os.path.join(FIG_DIR, "emotion_counts.png")
    plt.savefig(out1)
    print(f"Saved {out1}")

    # Avg latency chart
    al_vals = [avg_latency[e] for e in emos]
    plt.figure()
    plt.bar(emos, al_vals)
    plt.title("Average Latency by Emotion (ms)")
    plt.xlabel("Emotion")
    plt.ylabel("Avg Latency (ms)")
    plt.tight_layout()
    out2 = os.path.join(FIG_DIR, "avg_latency_by_emotion.png")
    plt.savefig(out2)
    print(f"Saved {out2}")

if __name__ == "__main__":
    main()
