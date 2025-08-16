from typing import Dict, Any, Optional
from backend.trans import translate_text
from backend.predict_disease_dl import analyze_symptoms_text

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
        # Bước 1: Nhận diện ngôn ngữ (nếu không được cung cấp)
        if not user_lang:
            detect_result = translate_text(symptoms_text, src="auto", dest="en")
            if detect_result.get("error"):
                return {"error": True, "message": "Không thể nhận diện ngôn ngữ"}
            user_lang = detect_result["src"]
        
        # Bước 2: Dịch sang tiếng Việt (nếu không phải tiếng Việt)
        vietnamese_text = symptoms_text
        if user_lang != "vi":
            translate_to_vi = translate_text(symptoms_text, src=user_lang, dest="vi")
            if translate_to_vi.get("error"):
                return {"error": True, "message": "Không thể dịch sang tiếng Việt"}
            vietnamese_text = translate_to_vi["translated"]
        
        # Bước 3: AI chẩn đoán (tiếng Việt)
        diagnosis_result = analyze_symptoms_text(vietnamese_text)
        if diagnosis_result.get("error"):
            return diagnosis_result
        
        # Bước 4: Dịch kết quả về ngôn ngữ người dùng
        translated_advice = diagnosis_result.get("advice", "")
        if user_lang != "vi" and translated_advice:
            advice_translation = translate_text(translated_advice, src="vi", dest=user_lang)
            if not advice_translation.get("error"):
                diagnosis_result["advice"] = advice_translation["translated"]
                diagnosis_result["advice_original"] = translated_advice
        
        # Bước 5: Trả về kết quả với metadata
        return {
            "ok": True,
            "user_language": user_lang,
            "original_symptoms": symptoms_text,
            "vietnamese_symptoms": vietnamese_text,
            "diagnosis": diagnosis_result,
            "pipeline": "multilang"
        }
        
    except Exception as e:
        return {"error": True, "message": f"Lỗi pipeline: {str(e)}"}