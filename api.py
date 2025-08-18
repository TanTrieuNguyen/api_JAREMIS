from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, importlib.util
from backend.multilang_diagnosis import multilang_diagnose
from backend.trans import translate_text, languages20

# nạp module dự đoán
base_dir = os.path.dirname(__file__)
predict_path = os.path.join(base_dir, "backend", "predict_disease_dl.py")
spec = importlib.util.spec_from_file_location("predict_module", predict_path)
predict_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(predict_module)

app = Flask(__name__, static_folder=".", static_url_path="")
app.config['JSON_AS_ASCII'] = False
CORS(app)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "up"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True, silent=True) or {}
    symptoms = data.get("symptoms")
    top_k = int(data.get("top_k", 5))
    if not symptoms or not isinstance(symptoms, list):
        return jsonify({"error": "Thiếu dữ liệu 'symptoms' dạng list"}), 400
    try:
        return jsonify(predict_module.predict_disease(symptoms, top_k=top_k))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/translate", methods=["POST"])
def api_translate():
    body = request.get_json(force=True, silent=True) or {}
    text = (body.get("text") or "").strip()
    src = (body.get("src") or "auto").strip()
    dest = (body.get("dest") or "vi").strip()
    return jsonify(translate_text(text, src=src, dest=dest))

@app.route("/api/multilang/languages", methods=["GET"])
def api_langs():
    return jsonify(languages20())

@app.route("/api/multilang/diagnose", methods=["POST"])
def api_multilang():
    body = request.get_json(force=True, silent=True) or {}
    symptoms_text = (body.get("symptoms") or "").strip()
    user_lang = (body.get("language") or "").strip() or None
    if not symptoms_text:
        return jsonify({"error": True, "message": "Vui lòng nhập triệu chứng"}), 400
    return jsonify(multilang_diagnose(symptoms_text, user_lang))
# route để test service luôn hoạt động
@app.route("/ping")
def ping():
    return jsonify({"msg": "pong"})


# vòng lặp nền đếm số để không bị sleep
def keep_alive_counter():
    i = 1
    while True:
        print(f"Counter: {i}")
        i += 1
        time.sleep(30)  # mỗi 30s tăng số 1 lần

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sẽ cấp PORT ngẫu nhiên
    app.run(host="0.0.0.0", port=port)


