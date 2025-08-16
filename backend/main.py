import os
import sys
import json
import uuid
from typing import List, Dict, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.speech_to_text import convert_audio_to_text
from backend.diagnosis import diagnose_and_suggest
from backend.tts import speak
from backend.train_disease_model_dl import train_model
from backend.predict_disease_dl import predict_disease
from backend.who_api import get_popular_diseases

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()


class DiseaseRequest(BaseModel):
    symptoms: List[str]
    lat: Optional[float] = None
    lng: Optional[float] = None


@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...)):
    file_location = f"temp_{uuid.uuid4().hex}.wav"
    try:
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)

        text = convert_audio_to_text(file_location)
        result = diagnose_and_suggest(text)
        diagnosis = result.get("Hành động gợi ý", {}).get("Hành động khuyến nghị", "Không rõ")
        mp3_path = speak(diagnosis)
        audio_url = f"/responses/audio/{os.path.basename(mp3_path)}"
        return {"diagnosis": diagnosis, "audio_url": audio_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý audio: {str(e)}")
    finally:
        if os.path.exists(file_location):
            try:
                os.remove(file_location)
            except Exception:
                pass


@app.get("/responses/audio/{filename}")
async def get_audio(filename: str):
    path = os.path.join("backend", "responses", "audio", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Không tìm thấy file audio")
    return FileResponse(path)


@app.post("/train/model")
async def train_ai_model():
    try:
        train_model()
        return {"status": "success", "message": "Đã huấn luyện lại model"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi huấn luyện: {str(e)}")


@app.post("/predict/disease")
async def predict_disease_api(req: DiseaseRequest):
    try:
        result = predict_disease(req.symptoms, lat=req.lat, lng=req.lng)
        return {"symptoms": req.symptoms, "prediction": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi dự đoán: {str(e)}")


@app.get("/model/info")
async def get_model_info():
    try:
        with open('backend/models/symptoms_list.json', 'r', encoding='utf-8') as f:
            symptoms = json.load(f)
        with open('backend/models/diseases_list.json', 'r', encoding='utf-8') as f:
            diseases = json.load(f)
        return {
            "total_symptoms": len(symptoms),
            "total_diseases": len(diseases),
            "symptoms": symptoms,
            "diseases": diseases
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc thông tin model: {str(e)}")


@app.post("/add/training-data")
async def add_training_data(data: Dict):
    try:
        with open('backend/data/disease_symptom_mapping.json', 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        new_entry = {"disease": data["disease"], "symptoms": data["symptoms"]}
        mapping.append(new_entry)

        with open('backend/data/disease_symptom_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

        return {"status": "success", "message": "Đã thêm dữ liệu huấn luyện mới", "total_entries": len(mapping)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thêm dữ liệu: {str(e)}")


@app.get("/training-data")
async def get_training_data():
    try:
        with open('backend/data/disease_symptom_mapping.json', 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        return {"total_entries": len(mapping), "data": mapping}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc dữ liệu: {str(e)}")


@app.get("/who/popular-diseases")
async def who_popular_diseases():
    try:
        data = get_popular_diseases()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy dữ liệu WHO: {str(e)}")