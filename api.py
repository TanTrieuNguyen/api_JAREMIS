from flask import Flask, request, jsonify
from flask_cors import CORS   # thêm dòng này
import os, importlib.util

PREDICT_SCRIPT_PATH = os.path.join("backend", "predict_disease_dl.py")
spec = importlib.util.spec_from_file_location("predict_module", PREDICT_SCRIPT_PATH)
predict_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(predict_module)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)  # Cho phép tất cả domain gọi API (fix lỗi Failed to fetch)

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json or {}
        symptoms = data.get("symptoms")
        top_k = int(data.get("top_k", 5))

        if not symptoms or not isinstance(symptoms, list):
            return jsonify({"error": "Thiếu dữ liệu 'symptoms' dạng list"}), 400

        result = predict_module.predict_disease(symptoms)

        # Rút gọn xác suất
        probs = result.pop("all_probabilities", {})
        if isinstance(probs, dict):
            sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
            result["top_probabilities"] = [
                {"disease": k, "prob": v} for k, v in sorted_probs[:top_k]
            ]

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
