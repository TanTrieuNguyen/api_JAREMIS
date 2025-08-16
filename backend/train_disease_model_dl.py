import json
import numpy as np
from typing import Dict, Any

try:
    from tensorflow import keras
    from tensorflow.keras import layers
except ImportError:
    print("Warning: TensorFlow not installed. Please install with: pip install tensorflow")
    keras = None
    layers = None
import os

def train_model() -> Dict[str, Any]:
    """Hàm huấn luyện model AI"""
    if keras is None or layers is None:
        raise ImportError("TensorFlow is required but not installed")
    
    # Đọc dữ liệu mapping triệu chứng-bệnh (dạng list các dict)
    with open('backend/data/disease_symptom_mapping.json', encoding='utf-8') as f:
        mapping = json.load(f)

    # Lấy tất cả triệu chứng và bệnh duy nhất
    all_symptoms = sorted({symptom for item in mapping for symptom in item["symptoms"]})
    all_diseases = sorted({item["disease"] for item in mapping})

    # Tạo dữ liệu train
    X = []
    y = []
    for item in mapping:
        x_vec = [int(symptom in item["symptoms"]) for symptom in all_symptoms]
        X.append(x_vec)
        y.append(all_diseases.index(item["disease"]))

    X = np.array(X)
    y = np.array(y)

    # Xây dựng model
    model = keras.Sequential([
        layers.Input(shape=(len(all_symptoms),)),
        layers.Dense(128, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(len(all_diseases), activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    # Train
    model.fit(X, y, epochs=100, batch_size=8, validation_split=0.2)

    # Đảm bảo thư mục models tồn tại
    os.makedirs('backend/models', exist_ok=True)

    # Lưu model
    model.save('backend/models/disease_model_dl.h5')

    # Lưu danh sách triệu chứng và bệnh để dùng khi dự đoán
    with open('backend/models/symptoms_list.json', 'w', encoding='utf-8') as f:
        json.dump(all_symptoms, f, ensure_ascii=False)
    with open('backend/models/diseases_list.json', 'w', encoding='utf-8') as f:
        json.dump(all_diseases, f, ensure_ascii=False)
    
    return {
        "total_symptoms": len(all_symptoms),
        "total_diseases": len(all_diseases),
        "training_samples": len(X)
    }

# Chạy huấn luyện nếu file được chạy trực tiếp
if __name__ == "__main__":
    try:
        result = train_model()
        print("Huấn luyện hoàn thành:", result)
    except Exception as e:
        print(f"Lỗi huấn luyện: {e}")