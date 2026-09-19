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

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123jesus")

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def login_handler(path):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            token = "auth_" + secrets.token_hex(20)
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

    return jsonify({"status": "Login endpoint ready", "method": "POST"}), 200

if __name__ == "__main__":
    app.run(port=5002, debug=True)
