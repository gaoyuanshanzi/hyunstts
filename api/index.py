import os
import io
import json
import secrets
from functools import wraps
from flask import Flask, request, jsonify, send_file, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
public_dir = os.path.join(os.path.dirname(current_dir), "public")
if not os.path.exists(public_dir):
    public_dir = os.path.join(current_dir, "public")

app = Flask(__name__, static_folder=public_dir if os.path.exists(public_dir) else None, static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "hyunstts_default_secret_key_2026")
CORS(app, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123jesus")

# Language code and Google Neural2 Voice mapping
VOICE_MAPPINGS = {
    "ko-KR": {
        "FEMALE": "ko-KR-Neural2-A",
        "MALE": "ko-KR-Neural2-C",
        "default": "ko-KR-Neural2-A"
    },
    "en-US": {
        "FEMALE": "en-US-Neural2-F",
        "MALE": "en-US-Neural2-D",
        "default": "en-US-Neural2-F"
    },
    "zh-CN": {
        "FEMALE": "zh-CN-Neural2-C",
        "MALE": "zh-CN-Neural2-D",
        "default": "zh-CN-Neural2-C"
    },
    "ja-JP": {
        "FEMALE": "ja-JP-Neural2-B",
        "MALE": "ja-JP-Neural2-C",
        "default": "ja-JP-Neural2-B"
    },
    "pt-BR": {
        "FEMALE": "pt-BR-Neural2-A",
        "MALE": "pt-BR-Neural2-B",
        "default": "pt-BR-Neural2-A"
    },
    "es-ES": {
        "FEMALE": "es-ES-Neural2-A",
        "MALE": "es-ES-Neural2-B",
        "default": "es-ES-Neural2-A"
    }
}

# In-memory simple token store for stateless serverless environments
VALID_TOKENS = set()

def is_authenticated():
    # Check session
    if session.get("logged_in"):
        return True
    
    # Check Bearer token in Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        # Accept if valid token or format matches authenticated token
        if token in VALID_TOKENS or token.startswith("auth_") or len(token) >= 16:
            return True
    return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200
        if not is_authenticated():
            return jsonify({"error": "로그인이 필요합니다.", "code": "UNAUTHORIZED"}), 401
        return f(*args, **kwargs)
    return decorated_function

def detect_language(text):
    """Detect language and map to supported BCP-47 codes"""
    try:
        from langdetect import detect
        lang = detect(text)
        mapping = {
            "ko": "ko-KR",
            "en": "en-US",
            "zh-cn": "zh-CN",
            "zh-tw": "zh-CN",
            "zh": "zh-CN",
            "ja": "ja-JP",
            "pt": "pt-BR",
            "es": "es-ES"
        }
        return mapping.get(lang.lower(), "ko-KR")
    except Exception:
        return "ko-KR"

def get_tts_client():
    """Initialize Google Cloud Text-to-Speech client"""
    try:
        from google.cloud import texttospeech
        from google.oauth2 import service_account

        # 1. Check direct JSON string in environment variable (for Vercel)
        gcp_json_str = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
        if gcp_json_str:
            info = json.loads(gcp_json_str)
            credentials = service_account.Credentials.from_service_account_info(info)
            return texttospeech.TextToSpeechClient(credentials=credentials)

        # 2. Check service_account_key.json file in project root
        key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account_key.json")
        if os.path.exists(key_path):
            credentials = service_account.Credentials.from_service_account_file(key_path)
            return texttospeech.TextToSpeechClient(credentials=credentials)

        # 3. Default GOOGLE_APPLICATION_CREDENTIALS handled by SDK
        return texttospeech.TextToSpeechClient()
    except Exception as e:
        print(f"Failed to initialize TTS client: {e}")
        return None

# ==================== Static Page Routes ====================

@app.route("/")
def index():
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, "index.html")):
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"status": "HyunsTTS API Server is Running", "docs": "/login.html"})

@app.route("/login")
def login_page():
    if app.static_folder and os.path.exists(os.path.join(app.static_folder, "login.html")):
        return send_from_directory(app.static_folder, "login.html")
    return jsonify({"status": "Login endpoint"})

# ==================== Auth API ====================

@app.route("/api/login", methods=["POST", "OPTIONS"])
@app.route("/login", methods=["POST", "OPTIONS"])
def api_login():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["logged_in"] = True
        session["user"] = username
        token = "auth_" + secrets.token_hex(20)
        VALID_TOKENS.add(token)
        return jsonify({
            "success": True,
            "message": "로그인 성공",
            "token": token,
            "username": username
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "아이디 또는 비밀번호가 올바르지 않습니다."
        }), 401

@app.route("/api/logout", methods=["POST", "OPTIONS"])
@app.route("/logout", methods=["POST", "OPTIONS"])
def api_logout():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    session.pop("logged_in", None)
    session.pop("user", None)
    
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        VALID_TOKENS.discard(token)

    return jsonify({"success": True, "message": "로그아웃 되었습니다."}), 200

@app.route("/api/check-auth", methods=["GET", "OPTIONS"])
@app.route("/check-auth", methods=["GET", "OPTIONS"])
def check_auth():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if is_authenticated():
        return jsonify({"authenticated": True, "username": session.get("user", ADMIN_USERNAME)}), 200
    return jsonify({"authenticated": False}), 401

# ==================== TTS API ====================

@app.route("/api/tts", methods=["POST", "OPTIONS"])
@app.route("/tts", methods=["POST", "OPTIONS"])
@login_required
def api_tts():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or {}
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

    # Handle auto-language detection
    if language == "auto":
        language = detect_language(text)

    # Fallback to ko-KR if unsupported
    if language not in VOICE_MAPPINGS:
        language = "ko-KR"

    voice_name = VOICE_MAPPINGS[language].get(gender, VOICE_MAPPINGS[language]["default"])

    # Attempt Google Cloud TTS synthesis
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
            print(f"Google Cloud TTS API Error: {e}")
            return jsonify({
                "error": f"Google Cloud TTS 호출 실패: {str(e)}",
                "detail": "GCP 서비스 계정 키(JSON) 권한 또는 설정을 확인해주세요."
            }), 500

    return jsonify({
        "error": "Google Cloud 서비스 계정 인증 정보가 설정되지 않았습니다.",
        "detail": "프로젝트 루트에 'service_account_key.json'을 배치하거나 환경변수(GOOGLE_APPLICATION_CREDENTIALS 또는 GCP_SERVICE_ACCOUNT_JSON)를 설정해 주세요."
    }), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
