import os
import json
from typing import List, Dict, Any, Optional
import numpy as np
import unicodedata
import re

# Dùng tf.keras (TF 2.12)
try:
    import tensorflow as tf
    keras = tf.keras
except ImportError:
    print("Warning: TensorFlow not installed. Please install with: pip install tensorflow")
    keras = None

# Thư viện ngoài (tùy chọn)
try:
    import requests
except ImportError:
    requests = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from rapidfuzz import process as rf_process  # tùy chọn để fuzzy match tốt hơn
except Exception:
    rf_process = None

# Model và danh sách triệu chứng/bệnh
model: Optional[Any] = None
all_symptoms: List[str] = []
all_diseases: List[str] = []


def load_model() -> None:
    """Load model và dữ liệu."""
    global model, all_symptoms, all_diseases
    if keras is None:
        raise ImportError("TensorFlow is required but not installed")
    model = keras.models.load_model('backend/models/disease_model_dl.h5')
    with open('backend/models/symptoms_list.json', encoding='utf-8') as f:
        all_symptoms = json.load(f)
    with open('backend/models/diseases_list.json', encoding='utf-8') as f:
        all_diseases = json.load(f)


def evaluate_severity(disease: str, confidence: float, symptoms: List[str]) -> Dict[str, Any]:
    """
    Trả về:
      - severity_score: 0..1
      - severity_level: "Cao" | "Trung bình" | "Thấp"
      - should_visit_hospital: bool
    Ưu tiên gọi API nếu .env có SEVERITY_API_URL (+ SEVERITY_API_KEY), nếu không dùng heuristic nội bộ.
    """
    # 1) API ngoài nếu có cấu hình
    try:
        if load_dotenv:
            load_dotenv(dotenv_path='backend/.env')
        api_url = os.getenv("SEVERITY_API_URL")
        api_key = os.getenv("SEVERITY_API_KEY")
        if api_url and requests:
            payload = {"disease": disease, "confidence": confidence, "symptoms": symptoms}
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                data = resp.json()
                score = float(data.get("severity_score", 0.0))
                score = max(0.0, min(1.0, score))
                level = data.get("severity_level") or ("Cao" if score >= 0.7 else ("Trung bình" if score >= 0.5 else "Thấp"))
                return {
                    "severity_score": score,
                    "severity_level": level,
                    "should_visit_hospital": bool(data.get("should_visit_hospital", score >= 0.7)),
                }
    except Exception:
        pass

    # 2) Heuristic nội bộ
    disease_lc = (disease or "").lower()
    CRITICAL_NAME_KWS = [
        "nhồi máu", "đột quỵ", "xuất huyết", "suy tim", "suy thận", "ung thư", "nhiễm trùng huyết",
        "viêm màng não", "viêm cơ tim", "tắc mạch", "phình", "sốc", "suy hô hấp", "hoại tử"
    ]
    RED_FLAG_SYMPTOMS = {
        "đau ngực", "khó thở", "mất ý thức", "liệt", "yếu nửa người", "co giật",
        "sốt cao", "nôn ra máu", "đi ngoài ra máu", "đau đầu dữ dội", "đau bụng dữ dội",
        "đau ngực dữ dội", "chảy máu không cầm", "vàng da", "lơ mơ", "đau mắt dữ dội"
    }
    syms = {s.strip().lower() for s in (symptoms or [])}
    has_critical_name = any(kw in disease_lc for kw in CRITICAL_NAME_KWS)
    red_flag_hits = sum(1 for s in syms if s in RED_FLAG_SYMPTOMS)

    score = 0.0
    score += 0.35 * max(0.0, min(1.0, confidence))
    score += 0.4 if has_critical_name else 0.0
    score += min(0.35, 0.15 * red_flag_hits)

    score = max(0.0, min(1.0, score))
    level = "Cao" if score >= 0.7 else ("Trung bình" if score >= 0.5 else "Thấp")
    should_go = score >= 0.7 or red_flag_hits >= 2

    return {
        "severity_score": score,
        "severity_level": level,
        "should_visit_hospital": should_go,
    }


def _fetch_popular_diseases() -> List[str]:
    """Lấy danh sách bệnh phổ biến từ WHO API (nếu có)."""
    try:
        from backend.who_api import get_popular_diseases
        data = get_popular_diseases()
        items = data.get("data", data) if isinstance(data, dict) else data
        names: List[str] = []
        for it in items or []:
            if isinstance(it, dict):
                name = it.get("name") or it.get("disease") or it.get("title")
                if name:
                    names.append(str(name).lower())
            elif isinstance(it, str):
                names.append(it.lower())
        return names
    except Exception:
        return []


def get_advice(disease: str, confidence: float, symptoms: List[str],
               severity_level: Optional[str] = None, should_visit_hospital: Optional[bool] = None) -> str:
    """Sinh lời khuyên đơn giản + động viên."""
    import random

    if severity_level is None or should_visit_hospital is None:
        sev = evaluate_severity(disease, confidence, symptoms or [])
        severity_level = sev["severity_level"]
        should_visit_hospital = sev["should_visit_hospital"]

    try:
        with open('backend/data/disease_symptom_mapping.json', encoding='utf-8') as f:
            _ = {e.get("disease", "").lower() for e in json.load(f) if isinstance(e, dict)}
    except Exception:
        pass

    funny_tips = [
        "Nhớ giữ tinh thần lạc quan nhé!", "Nghỉ ngơi hợp lý, uống đủ nước nha!",
        "Bạn là chiến binh, mọi chuyện sẽ ổn!", "Nếu mệt, hãy nhờ người thân hỗ trợ!",
        "Ăn uống lành mạnh và ngủ đủ giấc!", "Mang sạc dự phòng nếu phải đi viện nhé!"
    ]

    parts: List[str] = []
    pop_names = _fetch_popular_diseases()
    if disease and disease.lower() in pop_names:
        parts.append("Bệnh này đang khá phổ biến, bạn nên theo dõi kỹ triệu chứng.")

    if should_visit_hospital:
        parts.append(f"Mức độ {severity_level}. Bạn nên đến cơ sở y tế sớm.")
    else:
        if severity_level == "Trung bình":
            parts.append("Tình trạng trung bình. Nghỉ ngơi, uống đủ nước và theo dõi 24–48 giờ.")
        else:
            parts.append("Tình trạng nhẹ. Nghỉ ngơi và theo dõi thêm.")

    parts.append(random.choice(funny_tips))
    return " ".join(parts)


def _vn_norm(s: str) -> str:
    """Chuẩn hóa tiếng Việt: lower, trim, bỏ dấu, rút gọn khoảng trắng."""
    if not s:
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _load_symptom_synonyms() -> Dict[str, str]:
    """
    Đọc backend/data/symptom_synonyms.json (tùy chọn).
    Định dạng gợi ý:
    {
      "ho khan": ["ho kh", "ho khô", "cơn ho khan"],
      "sốt": ["sot", "sốt nhẹ", "sốt cao"]
    }
    Trả về map token_norm -> canonical_symptom_trong_all_symptoms (nếu khớp).
    """
    tok2canon: Dict[str, str] = {}
    try:
        with open("backend/data/symptom_synonyms.json", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Map all_symptoms đã chuẩn hóa -> bản gốc
            canon_sym_map = { _vn_norm(s): s for s in (all_symptoms or []) }
            for canon, syns in data.items():
                canon_key = _vn_norm(str(canon))
                if canon_key not in canon_sym_map:
                    # Nếu canonical chưa có trong model, bỏ qua để tránh lệch cột
                    continue
                canon_name = canon_sym_map[canon_key]
                for w in (syns or []):
                    if isinstance(w, str):
                        tok2canon[_vn_norm(w)] = canon_name
                # Cho phép token đúng canonical cũng map về chính nó
                tok2canon[canon_key] = canon_name
    except Exception:
        pass
    return tok2canon


def _normalize_input_symptoms(raw_inputs: List[str]) -> List[str]:
    """
    Biến danh sách triệu chứng người dùng -> danh sách triệu chứng đúng cột model.
    - Ưu tiên map synonyms
    - Sau đó exact match theo chuẩn hóa
    - Cuối cùng fuzzy match (rapidfuzz) nếu có, ngưỡng 90
    """
    if not raw_inputs:
        return []
    canon_sym_map = { _vn_norm(s): s for s in (all_symptoms or []) }
    synonyms = _load_symptom_synonyms()
    out: List[str] = []
    seen = set()

    for token in raw_inputs:
        t = _vn_norm(token)
        mapped = None

        # 1) synonyms
        if t in synonyms:
            mapped = synonyms[t]
        # 2) exact theo chuẩn hóa
        elif t in canon_sym_map:
            mapped = canon_sym_map[t]
        # 3) fuzzy match
        elif rf_process:
            choices = list(canon_sym_map.keys())
            best = rf_process.extractOne(t, choices, score_cutoff=90)
            if best:
                mapped = canon_sym_map[best[0]]

        if mapped and mapped not in seen:
            seen.add(mapped)
            out.append(mapped)
    return out


def predict_disease(input_symptoms: List[str]) -> Dict[str, Any]:
    """Dự đoán bệnh, đánh giá mức độ và sinh lời khuyên (không dùng GPS/Google Maps)."""
    if model is None:
        load_model()

    # CHUẨN HÓA TRIỆU CHỨNG
    norm_syms = _normalize_input_symptoms([s for s in (input_symptoms or []) if isinstance(s, str)])
    sym_set = set(norm_syms)

    input_vec = np.array([[int(symptom in sym_set) for symptom in all_symptoms]], dtype=np.float32)
    pred = model.predict(input_vec, verbose=0)
    probs = pred[0]
    idx = int(np.argmax(probs))
    predicted_disease = all_diseases[idx]
    confidence = float(probs[idx])

    # Top-K gợi ý
    top_k_idx = np.argsort(probs)[-3:][::-1]
    top_k = [{"disease": all_diseases[i], "prob": float(probs[i])} for i in top_k_idx]

    sev = evaluate_severity(predicted_disease, confidence, norm_syms or [])
    advice = get_advice(predicted_disease, confidence, norm_syms, sev["severity_level"], sev["should_visit_hospital"])

    return {
        "disease": predicted_disease,
        "confidence": confidence,
        "severity_level": sev["severity_level"],
        "severity_score": sev["severity_score"],
        "advice": advice,
        "should_visit_hospital": sev["should_visit_hospital"],
        "top_k": top_k,
        "normalized_symptoms": norm_syms,
        "all_probabilities": {d: float(p) for d, p in zip(all_diseases, probs)},
    }


if __name__ == "__main__":
    try:
        user_input = input("Nhập các triệu chứng cách nhau bởi dấu phẩy (ví dụ: đau đầu, sốt, ho):\n> ")
        input_symptoms = [sym.strip() for sym in user_input.split(',') if sym.strip()]
        result = predict_disease(input_symptoms)
        print("→ Dự đoán bệnh:", result["disease"])
        print("→ Độ tự tin:", result["confidence"])
        print("→ Mức độ nghiêm trọng:", result["severity_level"], f"(score={result['severity_score']:.2f})")
        print("→ Lời khuyên:", result["advice"])
    except Exception as e:
        print(f"Lỗi: {e}")