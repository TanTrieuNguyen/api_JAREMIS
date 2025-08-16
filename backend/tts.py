from gtts import gTTS
import os
import uuid

def text_to_speech(text, lang="vi"):
    """
    Chuyển văn bản thành giọng nói và lưu thành file MP3 tại responses/audio/jaremis_reply.mp3
    Args:
        text (str): Văn bản cần chuyển thành giọng nói.
        lang (str): Ngôn ngữ (mặc định: tiếng Việt).
    """
    output_path = os.path.join("responses", "audio", "jaremis_reply.mp3")
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)
    print(f"Đã lưu file âm thanh tại {output_path}")

def speak(text, lang="vi"):
    """
    Chuyển văn bản thành giọng nói và lưu thành file MP3 với tên duy nhất.
    """
    filename = f"backend/responses/audio/jaremis_reply_{uuid.uuid4().hex}.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename

# Ví dụ sử dụng:
# text_to_speech("Xin chào, tôi là JAREMIS.")