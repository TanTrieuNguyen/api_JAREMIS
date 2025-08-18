# File: backend/diagnosis.py

import os
import requests
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Nạp biến môi trường từ .env (ưu tiên .env ở thư mục gốc dự án; fallback backend/.env)
ROOT_DIR = Path(__file__).resolve().parents[1]
DOTENV_PATH = ROOT_DIR / ".env"
if not DOTENV_PATH.exists():
    DOTENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=False)

# Import các module nội bộ (giữ nguyên nếu bạn đã có)
from analyzer import extract_symptoms
from decision_logic import make_decision
from backend.predict_disease_dl import predict_disease as base_predict
from backend.who_api import get_popular_diseases
from backend.multilang_diagnosis import multilang_diagnose

# ===== EndlessMedical API (RapidAPI) =====
ENDLESS_API_KEY = os.getenv("ENDLESSMEDICAL_API_KEY", "")
ENDLESS_BASE_URL = "https://endlessmedicalapi1.p.rapidapi.com"
ENDLESS_INIT_SESSION_URL = f"{ENDLESS_BASE_URL}/InitSession"
ENDLESS_UPDATE_FEATURE_URL = f"{ENDLESS_BASE_URL}/UpdateFeature"
ENDLESS_GET_DIAGNOSIS_URL = f"{ENDLESS_BASE_URL}/GetDiagnosis"
ENDLESS_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "endlessmedicalapi1.p.rapidapi.com",
    "x-rapidapi-key": ENDLESS_API_KEY
}

# ===== NIH Clinical Tables (ICD-10) =====
CLINICAL_TABLES_API = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"

# ===== MyHealthfinder API =====
MYHEALTHFINDER_API = "https://health.gov/myhealthfinder/api/v3/topicsearch.json"


def call_endless_api(symptoms: List[str]) -> Dict[str, Any]:
    """
    Gửi triệu chứng đến EndlessMedical API để nhận chẩn đoán (top conditions).
    Trả về dict gồm session info và kết quả chẩn đoán (nếu có).
    """
    result: Dict[str, Any] = {"sessionId": None, "diagnosis": None, "raw": None}

    if not ENDLESS_API_KEY:
        raise RuntimeError("Thiếu ENDLESSMEDICAL_API_KEY trong .env")

    # 1) Tạo session
    session_resp = requests.get(ENDLESS_INIT_SESSION_URL, headers=ENDLESS_HEADERS, timeout=20)
    session_resp.raise_for_status()
    session_data = session_resp.json()
    session_id = session_data.get("SessionID") or session_data.get("SessionIDString") or session_data.get("result")
    result["sessionId"] = session_id

    # 2) Cập nhật các feature/triệu chứng
    # API yêu cầu tên feature chuẩn của họ; ở đây ta cứ gửi chuỗi văn bản để demo.
    # Tùy thực tế, bạn map "symptom text" -> feature name đúng chuẩn trước khi gọi API.
    for s in symptoms or []:
        payload = {
            "SessionID": session_id,
            "name": str(s),
            "value": "present"  # có thể cần "present"/"absent"/mức độ tùy API
        }
        uf = requests.post(ENDLESS_UPDATE_FEATURE_URL, headers=ENDLESS_HEADERS, json=payload, timeout=20)
        uf.raise_for_status()

    # 3) Lấy chẩn đoán
    diag_resp = requests.get(ENDLESS_GET_DIAGNOSIS_URL, headers=ENDLESS_HEADERS, params={"SessionID": session_id}, timeout=20)
    diag_resp.raise_for_status()
    diag_json = diag_resp.json()
    result["raw"] = diag_json

    # Chuẩn hóa kết quả top conditions (nếu có)
    # Endless trả định dạng khác nhau tùy phiên bản; ta cố gắng trích top conditions.
    candidates = []
    if isinstance(diag_json, dict):
        # một số field thường gặp: "Diseases", "Data", "Conditions"
        data = diag_json.get("Diseases") or diag_json.get("Data") or diag_json.get("Conditions") or diag_json.get("result")
        if isinstance(data, list):
            for it in data:
                if isinstance(it, dict):
                    name = it.get("Disease") or it.get("Name") or it.get("Condition")
                    prob = it.get("Probability") or it.get("Prob") or it.get("probability")
                    if name is not None and prob is not None:
                        try:
                            candidates.append({"name": str(name), "probability": float(prob)})
                        except Exception:
                            pass
        elif isinstance(data, dict):
            # đôi khi là { name: prob }
            for k, v in data.items():
                try:
                    candidates.append({"name": str(k), "probability": float(v)})
                except Exception:
                    pass

    # Sắp xếp theo xác suất giảm dần
    candidates.sort(key=lambda x: x.get("probability", 0.0), reverse=True)
    result["diagnosis"] = candidates
    return result


def search_clinical_table(term: str) -> Dict[str, Any]:
    """Tra ICD-10 từ NIH Clinical Tables."""
    r = requests.get(CLINICAL_TABLES_API, params={"terms": term, "sf": "code,name"}, timeout=20)
    r.raise_for_status()
    data = r.json()
    # Trả về dạng dễ dùng
    # data format: [index, numFound, [listResults], ...]
    out: Dict[str, Any] = {"term": term, "total": 0, "items": []}
    if isinstance(data, list) and len(data) >= 3 and isinstance(data[2], list):
        out["total"] = int(data[1]) if len(data) > 1 and isinstance(data[1], (int, str)) else len(data[2])
        for row in data[2]:
            # row: [code, name, ...]
            if isinstance(row, list) and len(row) >= 2:
                out["items"].append({"code": row[0], "name": row[1]})
    return out


def get_healthfinder_topics() -> Dict[str, Any]:
    """Lấy danh sách chủ đề sức khỏe từ MyHealthfinder."""
    r = requests.get(MYHEALTHFINDER_API, timeout=20)
    r.raise_for_status()
    data = r.json()
    items = []
    if isinstance(data, dict):
        items = data.get("Result", {}).get("Topics", []) or data.get("result", {}).get("topics", []) or []
    return {"items": items}


def calculate_who_boost(disease_name: str, popular_diseases: List[str]) -> float:
    """Tính boost factor dựa trên WHO data"""
    disease_lower = disease_name.lower().strip()
    
    # Exact match gets highest boost
    for i, pop_disease in enumerate(popular_diseases):
        if disease_lower == pop_disease.lower():
            return 0.3 - (i * 0.02)  # 0.3 for #1, 0.28 for #2, etc
    
    # Partial match gets medium boost  
    for i, pop_disease in enumerate(popular_diseases):
        if (disease_lower in pop_disease.lower() or 
            pop_disease.lower() in disease_lower):
            return 0.15 - (i * 0.01)  # Medium boost
    
    return 0.0  # No boost

def enhanced_predict_disease(input_symptoms: List[str], region: str = "Global") -> Dict[str, Any]:
    """AI chẩn đoán có tích hợp WHO epidemic data"""
    
    # 1. Base prediction từ model gốc
    base_result = base_predict(input_symptoms)
    
    # 2. Lấy WHO data
    try:
        popular_diseases = get_popular_diseases(region)
        who_data_available = len(popular_diseases) > 0
    except Exception as e:
        popular_diseases = []
        who_data_available = False
        print(f"WHO API error: {e}")
    
    # 3. Adjust probabilities with WHO data
    if who_data_available and "all_probabilities" in base_result:
        adjusted_probs = {}
        original_probs = base_result["all_probabilities"]
        
        for disease, prob in original_probs.items():
            who_boost = calculate_who_boost(disease, popular_diseases)
            # Apply boost: new_prob = original_prob + (boost * original_prob) 
            adjusted_prob = prob + (who_boost * prob)
            adjusted_probs[disease] = min(1.0, adjusted_prob)  # Cap at 1.0
        
        # Find new top prediction
        top_disease = max(adjusted_probs, key=adjusted_probs.get)
        top_confidence = adjusted_probs[top_disease]
        
        # Update result if different from base
        if top_disease != base_result["disease"]:
            base_result["disease"] = top_disease
            base_result["confidence"] = top_confidence
            base_result["who_adjusted"] = True
            base_result["original_disease"] = base_result.get("disease")
            base_result["original_confidence"] = base_result.get("confidence")
        
        # Update top-k with adjusted probabilities
        sorted_adj = sorted(adjusted_probs.items(), key=lambda x: x[1], reverse=True)
        base_result["top_k"] = [{"disease": d, "prob": p} for d, p in sorted_adj[:5]]
        base_result["all_probabilities"] = adjusted_probs
    
    # 4. Add WHO context
    base_result["who_context"] = {
        "data_available": who_data_available,
        "popular_diseases": popular_diseases[:10],  # Top 10
        "region": region,
        "boost_applied": who_data_available
    }
    
    return base_result

def enhanced_multilang_diagnose(symptoms_text: str, 
                               user_lang: Optional[str] = None,
                               region: str = "Global") -> Dict[str, Any]:
    """Multilang diagnosis với WHO integration"""
    try:
        # Bước 1-2: Language detection & translation (tương tự multilang_diagnosis.py)
        if not user_lang:
            from backend.trans import translate_text
            detect_result = translate_text(symptoms_text, src="auto", dest="en")
            if detect_result.get("error"):
                return {"error": True, "message": "Không thể nhận diện ngôn ngữ"}
            user_lang = detect_result["src"]
        
        vietnamese_text = symptoms_text
        if user_lang != "vi":
            from backend.trans import translate_text
            translate_to_vi = translate_text(symptoms_text, src=user_lang, dest="vi")
            if translate_to_vi.get("error"):
                return {"error": True, "message": "Không thể dịch sang tiếng Việt"}
            vietnamese_text = translate_to_vi["translated"]
        
        # Bước 3: Enhanced AI diagnosis với WHO data
        from backend.predict_disease_dl import _normalize_input_symptoms
        normalized_symptoms = _normalize_input_symptoms([vietnamese_text])
        diagnosis_result = enhanced_predict_disease(normalized_symptoms, region)
        
        # Bước 4: Translate advice back
        if user_lang != "vi" and diagnosis_result.get("advice"):
            from backend.trans import translate_text
            advice_translation = translate_text(diagnosis_result["advice"], src="vi", dest=user_lang)
            if not advice_translation.get("error"):
                diagnosis_result["advice"] = advice_translation["translated"]
                diagnosis_result["advice_original"] = diagnosis_result.get("advice")
        
        return {
            "ok": True,
            "user_language": user_lang,
            "original_symptoms": symptoms_text,
            "vietnamese_symptoms": vietnamese_text,
            "diagnosis": diagnosis_result,
            "pipeline": "enhanced_multilang_who"
        }
        
    except Exception as e:
        return {"error": True, "message": f"Enhanced diagnosis error: {str(e)}"}


def diagnose_and_suggest(text: str) -> Dict[str, Any]:
    """
    Pipeline: tách triệu chứng -> gọi EndlessMedical -> tạo khuyến nghị dựa trên decision_logic.
    """
    # 1) Trích xuất triệu chứng từ đoạn text người dùng
    try:
        symptoms = extract_symptoms(text) or []
    except Exception:
        symptoms = []

    # 2) Gọi EndlessMedical (có thể fail nếu API key bad)
    endless = {}
    try:
        endless = call_endless_api(symptoms)
    except Exception as e:
        endless = {"error": str(e)}

    # 3) Biến đổi dữ liệu đầu vào cho decision_logic
    top_conditions = endless.get("diagnosis") or []
    diagnosis_result = {
        "TopConditions": top_conditions[:5],
        "SessionID": endless.get("sessionId")
    }

    # 4) Quyết định hành động khuyến nghị
    logic = make_decision(diagnosis_result, symptoms)

    return {
        "Triệu chứng": symptoms,
        "Chẩn đoán EndlessMedical": diagnosis_result,
        "Khuyến nghị": logic,
        "Lỗi EndlessMedical": endless.get("error")
    }


if __name__ == "__main__":
    # Test nhanh trên terminal
    sample = input("Nhập mô tả triệu chứng: ")
    res = diagnose_and_suggest(sample)
    from pprint import pprint
    pprint(res)