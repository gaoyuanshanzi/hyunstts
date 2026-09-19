import os
import io
import json
import asyncio
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Language mappings for Google Cloud TTS & Edge Neural Voices
VOICE_MAPPINGS = {
    "ko-KR": {
        "FEMALE": {"gcp": "ko-KR-Neural2-A", "edge": "ko-KR-SunHiNeural"},
        "MALE": {"gcp": "ko-KR-Neural2-C", "edge": "ko-KR-InJoonNeural"}
    },
    "en-US": {
        "FEMALE": {"gcp": "en-US-Neural2-F", "edge": "en-US-JennyNeural"},
        "MALE": {"gcp": "en-US-Neural2-D", "edge": "en-US-GuyNeural"}
    },
    "zh-CN": {
        "FEMALE": {"gcp": "zh-CN-Neural2-C", "edge": "zh-CN-XiaoxiaoNeural"},
        "MALE": {"gcp": "zh-CN-Neural2-D", "edge": "zh-CN-YunxiNeural"}
    },
    "ja-JP": {
        "FEMALE": {"gcp": "ja-JP-Neural2-B", "edge": "ja-JP-NanamiNeural"},
        "MALE": {"gcp": "ja-JP-Neural2-C", "edge": "ja-JP-KeitaNeural"}
    },
    "pt-BR": {
        "FEMALE": {"gcp": "pt-BR-Neural2-A", "edge": "pt-BR-FranciscaNeural"},
        "MALE": {"gcp": "pt-BR-Neural2-B", "edge": "pt-BR-AntonioNeural"}
    },
    "es-ES": {
        "FEMALE": {"gcp": "es-ES-Neural2-A", "edge": "es-ES-ElviraNeural"},
        "MALE": {"gcp": "es-ES-Neural2-B", "edge": "es-ES-AlvaroNeural"}
    }
}

def detect_language(text):
    try:
        from langdetect import detect
        lang = detect(text).lower()
        mapping = {
            "ko": "ko-KR",
            "en": "en-US",
            "zh-cn": "zh-CN", "zh-tw": "zh-CN", "zh": "zh-CN",
            "ja": "ja-JP",
            "pt": "pt-BR",
            "es": "es-ES"
        }
        return mapping.get(lang, "ko-KR")
    except Exception:
        return "ko-KR"

def get_gcp_client():
    try:
        from google.cloud import texttospeech
        from google.oauth2 import service_account

        gcp_json_str = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
        if gcp_json_str:
            info = json.loads(gcp_json_str)
            credentials = service_account.Credentials.from_service_account_info(info)
            return texttospeech.TextToSpeechClient(credentials=credentials)

        key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account_key.json")
        if os.path.exists(key_path):
            credentials = service_account.Credentials.from_service_account_file(key_path)
            return texttospeech.TextToSpeechClient(credentials=credentials)

        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return texttospeech.TextToSpeechClient()
    except Exception as e:
        print(f"GCP init note: {e}")
    return None

async def synthesize_edge_tts(text, voice_name, speed=1.0, pitch=0.0):
    """Synthesize high-definition MP3 audio using Edge Neural Voices"""
    import edge_tts

    # Convert speaking rate (0.5x ~ 2.0x) to Edge TTS rate string (+10%, -20%)
    rate_percent = int((speed - 1.0) * 100)
    rate_str = f"{rate_percent:+d}%"

    # Convert pitch (-20 ~ +20) to Edge TTS pitch string (+5Hz, -10Hz)
    pitch_int = int(pitch)
    pitch_str = f"{pitch_int:+d}Hz"

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_name,
        rate=rate_str,
        pitch=pitch_str
    )

    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    return b"".join(audio_chunks)

def process_tts(data):
    text = data.get("text", "").strip()
    language = data.get("language", "auto")
    gender = data.get("gender", "FEMALE").upper()
    if gender not in ("FEMALE", "MALE"):
        gender = "FEMALE"

    try:
        speaking_rate = float(data.get("speed", 1.0))
        speaking_rate = max(0.5, min(speaking_rate, 2.0))
    except (ValueError, TypeError):
        speaking_rate = 1.0

    try:
        pitch = float(data.get("pitch", 0.0))
        pitch = max(-20.0, min(pitch, 20.0))
    except (ValueError, TypeError):
        pitch = 0.0

    if not text:
        return jsonify({"error": "음성으로 변환할 텍스트를 입력해주세요."}), 400

    if language == "auto":
        language = detect_language(text)

    if language not in VOICE_MAPPINGS:
        language = "ko-KR"

    lang_voice = VOICE_MAPPINGS[language][gender]

    # 1. Attempt Google Cloud Official Neural2 TTS (if credentials configured)
    gcp_client = get_gcp_client()
    if gcp_client:
        try:
            from google.cloud import texttospeech

            synthesis_input = texttospeech.SynthesisInput(text=text)
            ssml_gender = (
                texttospeech.SsmlVoiceGender.MALE if gender == "MALE"
                else texttospeech.SsmlVoiceGender.FEMALE
            )
            voice = texttospeech.VoiceSelectionParams(
                language_code=language,
                name=lang_voice["gcp"],
                ssml_gender=ssml_gender
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch
            )
            response = gcp_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            if response.audio_content and len(response.audio_content) > 100:
                return send_file(
                    io.BytesIO(response.audio_content),
                    mimetype="audio/mpeg",
                    as_attachment=False,
                    download_name="tts_audio.mp3"
                )
        except Exception as e:
            print(f"GCP synthesis exception, switching to Neural Engine: {e}")

    # 2. High-Quality Neural AI Voice Engine (100% Reliable MP3 Generation)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data = loop.run_until_complete(
            synthesize_edge_tts(text, lang_voice["edge"], speaking_rate, pitch)
        )
        loop.close()

        if audio_data and len(audio_data) > 100:
            return send_file(
                io.BytesIO(audio_data),
                mimetype="audio/mpeg",
                as_attachment=False,
                download_name="tts_audio.mp3"
            )
        else:
            raise ValueError("Empty audio generated")
    except Exception as err:
        print(f"Neural engine synthesis error: {err}")
        return jsonify({
            "error": f"음성 합성에 실패했습니다: {str(err)}",
            "detail": "잠시 후 다시 시도해주세요."
        }), 500

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def catch_all(path):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        return process_tts(data)

    return jsonify({"status": "TTS endpoint ready", "method": "POST"}), 200

if __name__ == "__main__":
    app.run(port=5001, debug=True)
