# backend/utils/nlp.py
from transformers import pipeline

# DistilBERT emotion model (labels: anger, fear, joy, love, sadness, surprise)
_emotion = pipeline(
    task="text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
    return_all_scores=True  # always return all labels with scores
)

EMO_SET = {"joy", "sadness", "anger", "fear", "love", "surprise"}

def _normalize(preds):
    """
    HF pipeline returns either:
      - [ {'label': 'sadness', 'score': 0.73}, ... ]  (single list)
      - [ [ {'label': 'sadness', 'score': 0.73}, ... ] ] (list of lists)
    This makes it a flat list of dicts for single input strings.
    """
    if isinstance(preds, list) and preds and isinstance(preds[0], list):
        return preds[0]
    return preds

def analyze_emotion(text: str):
    """
    Returns:
      {
        'emotion': <top_label>,
        'confidence': <0..1>,
        'scores': {'joy':0.x, 'sadness':0.y, ...}
      }
    """
    raw = _emotion(text)
    preds = _normalize(raw)

    by_label = {p["label"]: float(p["score"]) for p in preds if p["label"] in EMO_SET}
    # guard against unexpected empty outputs
    if not by_label:
        return {"emotion": "joy", "confidence": 0.0, "scores": {}}

    top = max(by_label, key=by_label.get)
    return {
        "emotion": top,
        "confidence": round(by_label[top], 3),
        "scores": {k: round(v, 3) for k, v in by_label.items()}
    }
