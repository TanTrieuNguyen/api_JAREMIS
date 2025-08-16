# File: backend/decision_logic.py

from typing import Dict, List

def make_decision(diagnosis_result: Dict, symptoms: List[str]) -> Dict:
    """
    Phân tích kết quả chẩn đoán và triệu chứng để đưa ra hành động gợi ý
    Trả về gợi ý điều trị, mức độ nghiêm trọng và hành động kế tiếp.
    """

    recommendations = []
    severity = "Không xác định"
    go_to_hospital = False

    # 1. Phân tích kết quả từ EndlessMedical (nếu có)
    top_conditions = diagnosis_result.get("Diseases", [])
    if top_conditions:
        top_condition = top_conditions[0].get("Name", "")
        probability = top_conditions[0].get("Probability", 0)

        if probability > 0.8:
            severity = "Cao"
            go_to_hospital = True
            recommendations.append(f"Khả năng cao là: {top_condition} (xác suất {probability:.2%}). Nên đi khám bác sĩ sớm.")
        elif 0.4 < probability <= 0.8:
            severity = "Trung bình"
            recommendations.append(f"Có thể là: {top_condition}. Theo dõi triệu chứng và nghỉ ngơi.")
        else:
            severity = "Thấp"
            recommendations.append(f"Bệnh nhẹ hoặc không nghiêm trọng. Tiếp tục theo dõi triệu chứng.")

    # 2. Phân tích thêm nếu có triệu chứng cụ thể
    if "Fever" in symptoms:
        recommendations.append("Uống nhiều nước và dùng thuốc hạ sốt nếu sốt > 38.5°C.")
    if "Cough" in symptoms:
        recommendations.append("Dùng siro ho hoặc thuốc long đờm OTC. Tránh nơi bụi bẩn.")

    # 3. Đề xuất hành động tổng quát
    action = "Đi khám ngay" if go_to_hospital else "Theo dõi tại nhà và nghỉ ngơi"

    return {
        "Mức độ nghiêm trọng": severity,
        "Hành động khuyến nghị": action,
        "Gợi ý chăm sóc": recommendations
    }

# Kiểm tra nhanh
if __name__ == "__main__":
    from diagnosis import diagnose_and_suggest
    user_input = input("Nhập mô tả triệu chứng: ")
    diag = diagnose_and_suggest(user_input)
    logic = make_decision(diag.get("Chẩn đoán EndlessMedical", {}), diag.get("Triệu chứng", []))
    print(logic)
