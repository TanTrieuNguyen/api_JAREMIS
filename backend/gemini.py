from __future__ import annotations
import os, json
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv

# Load .env từ gốc dự án
ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
load_dotenv(dotenv_path=ENV if ENV.exists() else None, override=False)

# Gemini SDK
import google.generativeai as genai

API_KEY = os.getenv("GOOGLE_API_KEY") or ""
if not API_KEY:
    raise RuntimeError("Thiếu GOOGLE_API_KEY trong file .env ở thư mục gốc dự án.")
genai.configure(api_key=API_KEY)

app = Flask(__name__)

# ---- Gemini reasoning (inline 1 file) ----
SCHEMA_DESC = {
    "disclaimer": "string",
    "questions": [{"id":"string","text":"string","why":"string","options":["string"]}],
    "possible_factors": [{"name":"string","explanation":"string"}],
    "red_flags": [{"sign":"string","why":"string","action":"string"}],
    "next_steps": ["string"],
    "light_joke": "string"
}

def generate_health_intake(symptoms: str, humor: float = 0.25, language: str = "vi", context_facts: dict | None = None):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=(
            "Bạn là trợ lý sàng lọc triệu chứng (không phải bác sĩ). "
            "Đặt 8–12 câu hỏi khai thác bệnh sử (tuổi/giới, khởi phát/diễn tiến, vị trí/tính chất, sốt/đau, triệu chứng kèm, "
            "bệnh nền/thuốc/dị ứng, môi trường sống/làm việc, du lịch/phơi nhiễm, thói quen, mùa/vùng dịch, tiêm chủng, nghề nghiệp). "
            "Nêu các yếu tố có thể liên quan (phi chẩn đoán), dấu hiệu đỏ và bước tiếp theo an toàn. "
            "Nếu có dấu hiệu nguy cấp, khuyên đi cấp cứu ngay. Giọng điệu ấm áp, hài hước nhẹ. "
            "Chỉ trả về JSON đúng schema, không thêm text ngoài JSON."
        )
    )
    prompt = "\n".join([
        f"Ngôn ngữ: {language}",
        f"Mức hài hước (0-1): {max(0.0,min(1.0,humor))}",
        "Sinh JSON theo schema dưới, KHÔNG thêm text ngoài JSON.",
        "Yêu cầu:",
        "- 8–12 câu hỏi, mỗi câu có 'why', có thể có 'options'.",
        "- possible_factors: 4–7 mục, giải thích đơn giản (không chẩn đoán/kê đơn).",
        "- red_flags: 3–6 dấu hiệu + hành động rõ ràng.",
        "- next_steps: 4–7 bước an toàn, thực tế.",
        "- light_joke: 1 câu đùa nhẹ nhàng, lịch sự.",
        "Schema:",
        json.dumps(SCHEMA_DESC, ensure_ascii=False, indent=2),
        "Triệu chứng người dùng:",
        symptoms.strip(),
        "Bối cảnh hiện có:",
        json.dumps(context_facts or {}, ensure_ascii=False)
    ])
    resp = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.6,
            "top_p": 0.9,
            "max_output_tokens": 1200,
            "response_mime_type": "application/json",
        }
    )
    text = (resp.text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {"parse_error": True, "raw": text, "message": "Không parse được JSON từ Gemini."}
# -----------------------------------------

@app.get("/")
def index():
    return send_file(ROOT / "index.html")

@app.post("/api/triage")
def api_triage():
    body = request.get_json(force=True, silent=True) or {}
    symptoms = (body.get("symptoms") or "").strip()
    if not symptoms:
        return jsonify({"error": True, "message": "Vui lòng nhập mô tả triệu chứng."}), 400
    humor = float(body.get("humor") or 0.25)
    language = (body.get("language") or "vi").strip() or "vi"
    context_facts = body.get("context_facts") or {}
    try:
        data = generate_health_intake(symptoms, humor, language, context_facts)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

if __name__ == "__main__":
    # Chạy: py backend\web.py
    app.run(host="127.0.0.1", port=8000, debug=True)