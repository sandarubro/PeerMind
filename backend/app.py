# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import traceback

# project helpers (kept in utils/)
from utils.textnorm import normalize_text
from utils.nlp import analyze_emotion
from utils.db import init_db, log_message, get_metrics
from utils.safety import is_high_risk, SAFE_REPLY

# -------- Config --------
CONF_THRESH = 0.60  # if confidence < 0.60 -> mark as "unsure"

# -------- App --------
app = Flask(__name__)

# Allow everything during dev (web + emulator + phone)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers=["*"],
    methods=["GET", "POST", "OPTIONS"],
)

# Initialize SQLite on startup (db code is in utils/db.py)
init_db()


# -------- Routes --------
@app.get("/")
def root():
    return jsonify({"ok": True, "service": "FaceMind Backend", "version": "0.1"})


@app.get("/ping")
def ping():
    return jsonify({"ok": True})


@app.get("/metrics")
def metrics():
    """
    Return aggregated metrics collected by utils.db.get_metrics()
    Example structure returned depends on your db implementation.
    """
    try:
        m = get_metrics()
        return jsonify(m)
    except Exception:
        return jsonify({"error": "failed to gather metrics"}), 500


# Explicit OPTIONS handler (some browsers need this for fetch)
@app.route("/chat", methods=["OPTIONS"])
def chat_preflight():
    return ("", 204)


@app.post("/chat")
def chat():
    t0 = time.perf_counter()
    data = request.get_json(silent=True) or {}
    text = (data.get("message") or "").strip()
    if not text:
        return jsonify({"error": "message is required"}), 400

    # Normalize (Singlish/slang -> more standard English)
    norm = normalize_text(text)

    # 1) Safety/crisis check first (fast rule-based)
    try:
        if is_high_risk(norm):
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            # log 'crisis' explicitly with confidence 1.0 (so metrics can pick up)
            try:
                log_message(text, norm, "crisis", 1.0, latency_ms)
            except Exception:
                # logging errors should not break the response to the user
                app.logger.exception("Failed to log crisis message")
            return jsonify({
                "reply": SAFE_REPLY,
                "analysis": {
                    "emotion": "crisis",
                    "confidence": 1.0,
                    "scores": {},
                    "latency_ms": latency_ms
                }
            })
    except Exception:
        # Safety function failed unexpectedly; continue but log server-side
        app.logger.exception("is_high_risk raised an exception")

    # 2) Run emotion model (may be slower)
    try:
        emo = analyze_emotion(norm)  # expected: {'emotion': 'sadness', 'confidence': 0.xx, 'scores': {...}}
    except Exception:
        # If model fails, return a graceful fallback reply and log minimal info
        app.logger.exception("analyze_emotion failed")
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        try:
            log_message(text, norm, "error", 0.0, latency_ms)
        except Exception:
            app.logger.exception("Failed to log analysis error")
        return jsonify({
            "reply": "Sorry — something went wrong analysing that. Could you try rephrasing?",
            "analysis": {
                "emotion": "error",
                "confidence": 0.0,
                "scores": {},
                "latency_ms": latency_ms
            }
        }), 500

    # ensure values we expect exist and convert types safely
    emotion = emo.get("emotion", "unsure")
    try:
        conf = float(emo.get("confidence", 0.0))
    except Exception:
        conf = 0.0
    scores = emo.get("scores", {})

    # 3) Confidence gating
    if conf < CONF_THRESH:
        emotion = "unsure"

    # 4) Build reply
    reply_map = {
        "joy": "It’s good to hear something positive. What helped today? 🌸",
        "sadness": "I’m really sorry you’re feeling down. Want to talk about what led to this? 💙",
        "anger": "It sounds like something upset you. Want to unpack it together? 🔥",
        "fear": "That sounds worrying. Do you want to share what’s on your mind? 🌙",
        "love": "That feels warm and caring ❤️ Tell me more.",
        "surprise": "That was unexpected! How do you feel about it? ✨",
        "unsure": "I hear you. I’m here with you—say a bit more if you’d like 💛."
    }
    reply = reply_map.get(emotion, reply_map["unsure"])

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    # 5) Log to SQLite (utils/db.py handles schema + persistence)
    try:
        log_message(text, norm, emotion, conf, latency_ms, raw_scores=scores)
    except TypeError:
        # In case your log_message signature doesn't accept raw_scores, fallback to older call:
        try:
            log_message(text, norm, emotion, conf, latency_ms)
        except Exception:
            app.logger.exception("Failed to log message (fallback)")
    except Exception:
        app.logger.exception("Failed to log message")

    # 6) Return JSON with reply + analysis
    return jsonify({
        "reply": reply,
        "analysis": {
            "emotion": emotion,
            "confidence": conf,
            "scores": scores,
            "latency_ms": latency_ms
        }
    })


# -------- Main --------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # debug=True is helpful while developing; turn off for production
    app.run(host="0.0.0.0", port=port, debug=True)
