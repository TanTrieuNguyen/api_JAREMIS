import json
import os

# Đường dẫn file gốc và file xuất
input_path = 'symptom_keywords_2500.json'
output_path = 'symptom_keywords_2500_prolonged.json'

with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

prolonged = {}
for k, v in data.items():
    k_new = f"{k} kéo dài"
    # Nếu value đã có 'Prolonged' thì không thêm nữa
    if v and v.lower().startswith("prolonged "):
        v_new = v
    else:
        # Nếu value có dấu ':' hoặc ' - ', chỉ lấy phần đầu
        v_base = v.split(':')[0].split(' - ')[0] if v else v
        v_new = f"Prolonged {v_base[0].lower() + v_base[1:]}" if v_base else v
    prolonged[k_new] = v_new

# Gộp vào dict cũ (nếu muốn)
data.update(prolonged)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Đã sinh xong triệu chứng kéo dài!")
print("File lưu tại:", os.path.abspath(output_path))