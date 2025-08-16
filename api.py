import os
from flask import Flask, request, jsonify
import importlib.util
from flask_cors import CORS

PREDICT_SCRIPT_PATH = os.path.join("backend", "predict_disease_dl.py")
spec = importlib.util.spec_from_file_location("predict_module", PREDICT_SCRIPT_PATH)
predict_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(predict_module)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://tantrieunguyen.github.io/JAREMIS/"}})
app.config['JSON_AS_ASCII'] = False

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json or {}
        symptoms = data.get("symptoms")
        top_k = int(data.get("top_k", 5))

        if not symptoms or not isinstance(symptoms, list):
            return jsonify({"error": "Thiếu dữ liệu 'symptoms' dạng list"}), 400

        result = predict_module.predict_disease(symptoms)
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
    port = int(os.environ.get("PORT", 5000))  # Render sẽ cấp PORT ngẫu nhiên
    app.run(host="0.0.0.0", port=port)


