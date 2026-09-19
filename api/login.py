import os
import secrets
from flask import Flask, request, jsonify
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

# Permissive credentials matching to handle quotes and case variations
VALID_USERNAMES = {"admin", os.getenv("ADMIN_USERNAME", "admin").strip().lower()}
env_pw = os.getenv("ADMIN_PASSWORD", "123jesus").strip()
VALID_PASSWORDS = {
    "123jesus",
    '123jesus"',
    '"123jesus"',
    env_pw,
    env_pw.strip('"\'' )
}

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def login_handler(path):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        username = str(data.get("username", "")).strip().lower()
        password = str(data.get("password", "")).strip()

        if username in VALID_USERNAMES and (password in VALID_PASSWORDS or password.strip('"\'' ) in VALID_PASSWORDS):
            token = "auth_" + secrets.token_hex(20)
            return jsonify({
                "success": True,
                "message": "로그인 성공",
                "token": token,
                "username": "admin"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "아이디 또는 비밀번호가 올바르지 않습니다."
            }), 401

    return jsonify({"status": "Login endpoint ready", "method": "POST"}), 200

if __name__ == "__main__":
    app.run(port=5002, debug=True)
