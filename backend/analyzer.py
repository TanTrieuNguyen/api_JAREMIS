# File: backend/analyzer.py

from typing import List
import json
import os

# Đường dẫn đến file JSON chứa từ khóa triệu chứng
SYMPTOM_MAPPING_PATH = os.path.join(os.path.dirname(__file__), "data", "symptom_keywords.json")

def load_symptom_keywords() -> dict:
    """Tải từ khóa triệu chứng từ file JSON"""
    with open(SYMPTOM_MAPPING_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_symptoms(user_input: str) -> List[str]:
    """
    Phân tích câu đầu vào để tách ra danh sách triệu chứng.
    Ví dụ: "Tôi bị ho và sốt" => ["Cough", "Fever"]
    """
    symptom_keywords = load_symptom_keywords()
    normalized_input = user_input.lower()
    detected_symptoms = []

    for keyword, feature_name in symptom_keywords.items():
        if keyword.lower() in normalized_input:
            if feature_name not in detected_symptoms:
                detected_symptoms.append(feature_name)

    return detected_symptoms

# Kiểm tra nhanh (chạy thử từ terminal)
# Đã bỏ import ngược để tránh vòng lặp import
if __name__ == "__main__":
    input_text = input("Nhập triệu chứng: ")
    symptoms = extract_symptoms(input_text)
    print("Triệu chứng đã phát hiện:", symptoms)
    # Gợi ý: test pipeline chẩn đoán nếu muốn
    try:
        from diagnosis import diagnose_and_suggest
        result = diagnose_and_suggest(input_text)
        print("Kết quả chẩn đoán:", result)
    except ImportError:
        print("Không thể import diagnosis để test pipeline. Hãy chạy bằng: python -m backend.diagnosis từ thư mục gốc.")
