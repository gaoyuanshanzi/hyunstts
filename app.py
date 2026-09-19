import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.index import app

if __name__ == "__main__":
    print("=" * 60)
    print(" [HyunsTTS] 다국어 음성 합성 웹 서비스 시작")
    print(" 접속 주소: http://localhost:5000")
    print(" 기본 계정: ID: admin / PW: 123jesus")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
