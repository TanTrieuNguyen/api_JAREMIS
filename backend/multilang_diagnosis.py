import re
from typing import Dict, Any, Optional, List
from backend.trans import translate_text
from backend.predict_disease_dl import predict_disease

def _to_symptom_list(vn_text: str) -> List[str]:
    parts = re.split(r"[,\n;]+", vn_text)
    return [p.strip() for p in parts if p.strip()]

def multilang_diagnose(symptoms_text: str, user_lang: Optional[str] = None) -> Dict[str, Any]:
    """
    Pipeline đa ngôn ngữ:
    1. Nhận diện ngôn ngữ người dùng
    2. Dịch sang tiếng Việt để chẩn đoán
    3. AI chẩn đoán bệnh (tiếng Việt)
    4. Dịch kết quả về ngôn ngữ người dùng
    5. Trả về kết quả
    """
    try:
        symptoms_text = (symptoms_text or "").strip()
        if not symptoms_text:
            return {"error": True, "message": "Vui lòng nhập triệu chứng"}

        # 1) Nhận diện ngôn ngữ
        if not user_lang:
            detect = translate_text(symptoms_text, src="auto", dest="en")
            if detect.get("error"):
                return {"error": True, "message": "Không thể nhận diện ngôn ngữ"}
            user_lang = detect["src"]

        # 2) Dịch sang tiếng Việt
        vn_text = symptoms_text
        if user_lang != "vi":
            t = translate_text(symptoms_text, src=user_lang, dest="vi")
            if t.get("error"):
                return {"error": True, "message": "Không thể dịch sang tiếng Việt"}
            vn_text = t["translated"]

        # 3) Chuẩn hóa và chẩn đoán
        vn_symptoms = _to_symptom_list(vn_text)
        if not vn_symptoms:
            return {"error": True, "message": "Không thấy triệu chứng hợp lệ sau khi dịch"}
        diagnosis = predict_disease(vn_symptoms)

        # 4) Dịch lời khuyên về ngôn ngữ gốc
        adv = diagnosis.get("advice") or ""
        if adv and user_lang != "vi":
            back = translate_text(adv, src="vi", dest=user_lang)
            if not back.get("error"):
                diagnosis["advice_original"] = adv
                diagnosis["advice"] = back["translated"]

        return {
            "ok": True,
            "user_language": user_lang,
            "original_symptoms": symptoms_text,
            "vietnamese_symptoms": vn_symptoms,
            "diagnosis": diagnosis,
            "pipeline": "multilang"
        }
    except Exception as e:
        return {"error": True, "message": f"Lỗi pipeline: {e}"}