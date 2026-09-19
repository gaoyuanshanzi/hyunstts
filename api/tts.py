import os
import io
import json
import urllib.parse
import urllib.request
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

# Language mappings
VOICE_MAPPINGS = {
    "ko-KR": {"FEMALE": "ko-KR-Neural2-A", "MALE": "ko-KR-Neural2-C", "default": "ko-KR-Neural2-A", "tl": "ko"},
    "en-US": {"FEMALE": "en-US-Neural2-F", "MALE": "en-US-Neural2-D", "default": "en-US-Neural2-F", "tl": "en"},
    "zh-CN": {"FEMALE": "zh-CN-Neural2-C", "MALE": "zh-CN-Neural2-D", "default": "zh-CN-Neural2-C", "tl": "zh-CN"},
    "ja-JP": {"FEMALE": "ja-JP-Neural2-B", "MALE": "ja-JP-Neural2-C", "default": "ja-JP-Neural2-B", "tl": "ja"},
    "pt-BR": {"FEMALE": "pt-BR-Neural2-A", "MALE": "pt-BR-Neural2-B", "default": "pt-BR-Neural2-A", "tl": "pt"},
    "es-ES": {"FEMALE": "es-ES-Neural2-A", "MALE": "es-ES-Neural2-B", "default": "es-ES-Neural2-A", "tl": "es"}
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

def get_tts_client():
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
        print(f"GCP TTS Client init note: {e}")
    return None

def fallback_synthesize(text, lang_code):
    """Fallback TTS to guarantee audio output even before GCP credentials are set"""
    tl = VOICE_MAPPINGS.get(lang_code, {}).get("tl", "ko")
    encoded_text = urllib.parse.quote(text[:300]) # chunk if needed
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={tl}&client=tw-ob&q={encoded_text}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read()

def process_tts(data):
    text = data.get("text", "").strip()
    language = data.get("language", "auto")
    gender = data.get("gender", "FEMALE").upper()
    try:
        speaking_rate = float(data.get("speed", 1.0))
        speaking_rate = max(0.25, min(speaking_rate, 4.0))
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

    voice_name = VOICE_MAPPINGS[language].get(gender, VOICE_MAPPINGS[language]["default"])

    # 1. Attempt Google Cloud Official TTS
    client = get_tts_client()
    if client:
        try:
            from google.cloud import texttospeech

            synthesis_input = texttospeech.SynthesisInput(text=text)
            ssml_gender = (
                texttospeech.SsmlVoiceGender.MALE if gender == "MALE"
                else texttospeech.SsmlVoiceGender.FEMALE
            )
            voice = texttospeech.VoiceSelectionParams(
                language_code=language,
                name=voice_name,
                ssml_gender=ssml_gender
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch
            )
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            return send_file(
                io.BytesIO(response.audio_content),
                mimetype="audio/mpeg",
                as_attachment=False,
                download_name="tts_audio.mp3"
            )
        except Exception as e:
            print(f"GCP API Call Exception, trying fallback: {e}")

    # 2. Seamless Fallback TTS (guarantees MP3 output)
    try:
        audio_bytes = fallback_synthesize(text, language)
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="tts_audio.mp3"
        )
    except Exception as err:
        return jsonify({
            "error": f"음성 합성에 실패했습니다: {str(err)}",
            "detail": "GCP 서비스 계정 키를 설정하거나 네트워크를 확인해주세요."
        }), 500

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def catch_all(path):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # Handle TTS POST request
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        return process_tts(data)

    return jsonify({"status": "TTS endpoint ready", "method": "POST"}), 200

if __name__ == "__main__":
    app.run(port=5001, debug=True)
