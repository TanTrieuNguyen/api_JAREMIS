from typing import Dict, Any
from googletrans import Translator, LANGUAGES

_translator = Translator(service_urls=["translate.googleapis.com","translate.google.com"])

def translate_text(text: str, src: str = "auto", dest: str = "vi") -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {"error": True, "message": "Empty text"}
    try:
        res = _translator.translate(text, src=src, dest=dest)
        return {"ok": True, "src": res.src, "dest": res.dest, "text": text, "translated": res.text}
    except Exception as e:
        return {"error": True, "message": f"Translate failed: {e}"}

def languages20() -> Dict[str, str]:
    return {
        "en":"English","zh":"Chinese","hi":"Hindi","es":"Spanish","ar":"Arabic",
        "bn":"Bengali","pt":"Portuguese","ru":"Russian","ja":"Japanese","pa":"Punjabi",
        "de":"German","jv":"Javanese","ko":"Korean","fr":"French","te":"Telugu",
        "mr":"Marathi","tr":"Turkish","ta":"Tamil","vi":"Vietnamese","it":"Italian"
    }