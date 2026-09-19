from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route("/", defaults={"path": ""}, methods=["GET", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "OPTIONS"])
def check_handler(path):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if len(token) >= 10:
            return jsonify({"authenticated": True, "username": "admin"}), 200

    return jsonify({"authenticated": False}), 401

if __name__ == "__main__":
    app.run(port=5003, debug=True)
