from gtts import gTTS
import uuid
import os

def speak(text):
    tts = gTTS(text, lang="vi")
    filename = f"backend/responses/audio/jaremis_reply_{uuid.uuid4().hex}.mp3"
    tts.save(filename)
    return filename

def convert_audio_to_text(audio_path):
    return "Đây là kết quả giả lập từ giọng nói"

