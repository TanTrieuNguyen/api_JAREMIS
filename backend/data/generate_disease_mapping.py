import json
import random

# Đọc danh sách triệu chứng từ file symptom_keywords.json
with open('symptom_keywords.json', 'r', encoding='utf-8') as f:
    symptoms = list(json.load(f).keys())

# Sinh danh sách 2000 bệnh giả lập
diseases = [f"Bệnh số {i+1}" for i in range(2000)]

# Sinh mapping: mỗi bệnh có 3-7 triệu chứng ngẫu nhiên
mapping = []
for disease in diseases:
    chosen = random.sample(symptoms, k=random.randint(3, 7))
    mapping.append({
        "symptoms": chosen,
        "disease": disease
    })

# Ghi ra file JSON
with open('disease_symptom_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print("Đã sinh xong mapping 2000 bệnh vào file disease_symptom_mapping.json")