from typing import Dict, Any
from googletrans import Translator, LANGUAGES
from flask import Flask, request, jsonify

app = Flask(__name__)  # Tạo Flask app
_translator = Translator()

def translate_text(text: str, src: str = "auto", dest: str = "en") -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {"error": True, "message": "Empty text"}
    try:
        res = _translator.translate(text, src=src, dest=dest)
        return {"ok": True, "src": res.src, "dest": res.dest, "text": text, "translated": res.text}
    except Exception as e:
        return {"error": True, "message": str(e)}

def get_languages() -> Dict[str, str]:
    return LANGUAGES

@app.route("/api/translate", methods=["POST"])
def api_translate():
    body = request.get_json(force=True, silent=True) or {}
    text = (body.get("text") or "").strip()
    src = (body.get("src") or "auto").strip()
    dest = (body.get("dest") or "en").strip()
    return jsonify(translate_text(text, src=src, dest=dest))

@app.route("/api/translate/languages", methods=["GET"])
def api_languages():
    return jsonify(get_languages())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)