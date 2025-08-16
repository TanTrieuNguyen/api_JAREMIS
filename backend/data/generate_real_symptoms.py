import json
import random

# Danh sách triệu chứng thực tế (Việt-Anh) mẫu, cần mở rộng thêm cho đủ 2500 cặp
# Bạn có thể bổ sung thêm triệu chứng vào list này nếu muốn đa dạng hơn
symptoms_vi_en = [
    ("ho", "Cough"),
    ("sốt", "Fever"),
    ("đau đầu", "Headache"),
    ("đau bụng", "Abdominal pain"),
    ("buồn nôn", "Nausea"),
    ("nôn mửa", "Vomiting"),
    ("đau họng", "Sore throat"),
    ("khó thở", "Shortness of breath"),
    ("mệt mỏi", "Fatigue"),
    ("đau ngực", "Chest pain"),
    ("đau lưng", "Back pain"),
    ("đau khớp", "Joint pain"),
    ("đau cơ", "Muscle pain"),
    ("chóng mặt", "Dizziness"),
    ("ngứa", "Itching"),
    ("phát ban", "Rash"),
    ("rụng tóc", "Hair loss"),
    ("tê tay", "Numbness in hand"),
    ("tê chân", "Numbness in foot"),
    ("khó nuốt", "Difficulty swallowing"),
    ("khó ngủ", "Insomnia"),
    ("sưng chân", "Swollen legs"),
    ("mắt đỏ", "Red eyes"),
    ("mắt mờ", "Blurred vision"),
    ("chảy máu cam", "Nosebleed"),
    ("chảy nước mũi", "Runny nose"),
    ("tiêu chảy", "Diarrhea"),
    ("nước tiểu sẫm", "Dark urine"),
    ("co giật", "Seizures"),
    ("đau tai", "Ear pain"),
    ("đau mắt", "Eye pain"),
    ("đau răng", "Toothache"),
    ("đau cổ", "Neck pain"),
    ("đau vai", "Shoulder pain"),
    ("đau gối", "Knee pain"),
    ("đau bụng kinh", "Menstrual cramps"),
    ("đau tinh hoàn", "Testicular pain"),
    ("đau ngón tay", "Finger pain"),
    ("đau ngón chân", "Toe pain"),
    ("đau mông", "Buttock pain"),
    ("đau vùng chậu", "Pelvic pain"),
    ("đau vùng thắt lưng", "Lower back pain"),
    ("đau vùng bụng trên", "Upper abdominal pain"),
    ("đau vùng bụng dưới", "Lower abdominal pain"),
    ("đau vùng ngực trái", "Left chest pain"),
    ("đau vùng ngực phải", "Right chest pain"),
    ("đau vùng hông", "Hip pain"),
    ("đau vùng bẹn", "Groin pain"),
    ("đau vùng trán", "Forehead pain"),
    ("đau vùng thái dương", "Temple pain"),
    ("đau vùng gáy", "Nape pain"),
    ("đau vùng cằm", "Chin pain"),
    ("đau vùng má", "Cheek pain"),
    ("đau vùng lưng trên", "Upper back pain"),
    ("đau vùng lưng dưới", "Lower back pain"),
    ("đau vùng cổ tay", "Wrist pain"),
    ("đau vùng cổ chân", "Ankle pain"),
    ("đau vùng khuỷu tay", "Elbow pain"),
    ("đau vùng đầu gối", "Knee pain"),
    ("đau vùng ngón tay", "Finger pain"),
    ("đau vùng ngón chân", "Toe pain"),
    ("đau vùng bụng bên trái", "Left abdominal pain"),
    ("đau vùng bụng bên phải", "Right abdominal pain"),
    ("đau vùng ngực giữa", "Middle chest pain"),
    ("đau vùng lưng giữa", "Middle back pain"),
    # ... Bổ sung thêm triệu chứng thực tế tại đây ...
]

# Đọc thêm triệu chứng từ file nếu có
try:
    with open("symptom_keywords_clean.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for k, v in data.items():
            if (k, v) not in symptoms_vi_en:
                symptoms_vi_en.append((k, v))
except Exception:
    pass

# Loại bỏ trùng lặp
symptoms_vi_en = list(dict.fromkeys(symptoms_vi_en))

# Nếu chưa đủ 2500, sinh thêm triệu chứng giả định (có thể sửa lại cho thực tế hơn)
if len(symptoms_vi_en) < 2500:
    for i in range(len(symptoms_vi_en), 2500):
        vi = f"triệu chứng đặc biệt {i+1}"
        en = f"Special symptom {i+1}"
        symptoms_vi_en.append((vi, en))

# Trộn ngẫu nhiên để đa dạng
random.shuffle(symptoms_vi_en)

# Lấy đúng 2500 triệu chứng
symptoms_vi_en = symptoms_vi_en[:2500]

# Ghi ra file JSON
result = {vi: en for vi, en in symptoms_vi_en}
with open("symptom_keywords_2500.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Đã sinh file symptom_keywords_2500.json với 2500 triệu chứng thực tế (hoặc giả định nếu thiếu)")
