# HyunsTTS - 다국어 AI 음성 합성 웹 애플리케이션

Google Cloud Neural2 엔진 기반의 웹 다국어 Text-to-Speech(TTS) 서비스입니다. 모던한 화이트 모드(White Mode) UI와 관리자 인증 시스템을 제공하며, 고품질 오디오 즉시 재생 및 MP3 다운로드를 지원합니다.

---

## 🌟 주요 기능 및 특징

1. **다국어 음성 합성 (Neural2 HD)**:
   - 한국어 (`ko-KR`): `ko-KR-Neural2-A`(여성), `ko-KR-Neural2-C`(남성)
   - 미국 영어 (`en-US`): `en-US-Neural2-F`(여성), `en-US-Neural2-D`(남성)
   - 중국어 표준어 (`zh-CN`): `zh-CN-Neural2-C`(여성), `zh-CN-Neural2-D`(남성)
   - 일본어 (`ja-JP`): `ja-JP-Neural2-B`(여성), `ja-JP-Neural2-C`(남성)
   - 브라질 포르투갈어 (`pt-BR`): `pt-BR-Neural2-A`(여성), `pt-BR-Neural2-B`(남성)
   - 스페인어 (`es-ES`): `es-ES-Neural2-A`(여성), `es-ES-Neural2-B`(남성)
   - **자동 언어 감지 (`auto`)**: 입력된 텍스트의 언어를 실시간으로 판별하여 자동 매핑
2. **세부 음성 파라미터 조절**:
   - 음성 속도 (Speaking Rate: `0.5x` ~ `2.0x`)
   - 음성 피치 (Pitch: `-20.0` ~ `+20.0`)
   - 여성 / 남성 보이스 토글
3. **오디오 플레이어 및 원클릭 MP3 다운로드**:
   - 브라우저 내 즉시 스트리밍 및 자동 재생
   - 파일명 타임스탬프 자동 생성 (`tts_ko-KR_20260920_123456.mp3`)
4. **관리자 인증 보안**:
   - 기본 관리자 계정: `admin` / `123jesus`
   - 인증되지 않은 사용자의 메인 서비스 접근 방지 및 토큰 세션 관리
5. **Vercel Serverless Ready**:
   - Vercel 배포 최적화 (`api/index.py` Serverless Function 및 `public/` 정적 호스팅)

---

## 🚀 로컬 실행 방법 (Local Setup)

### 1. 가상환경 생성 및 의존성 패키지 설치

```bash
# 가상환경 생성 (선택 사항)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# 필수 패키지 설치
pip install -r requirements.txt
```

### 2. Google Cloud 서비스 계정 키 연동

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 선택 후 **Cloud Text-to-Speech API** 활성화
3. **IAM 및 관리자 > 서비스 계정** 메뉴에서 서비스 계정 생성
4. **키** 탭에서 **새 키 만들기 > JSON**을 선택하여 키 파일 다운로드
5. 다운로드한 JSON 파일을 프로젝트 루트 디렉토리에 `service_account_key.json` 이름으로 저장합니다.
   *(이 파일은 `.gitignore`에 등록되어 있어 GitHub에 유출되지 않습니다.)*

### 3. 서버 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000`으로 접속합니다.
- **관리자 ID**: `admin`
- **비밀번호**: `123jesus`

---

## ☁️ Vercel 배포 및 환경변수 설정

Vercel은 서버리스 환경이므로 JSON 파일 대신 **환경 변수**로 인증 정보를 주입합니다:

1. Vercel 프로젝트 대시보드 > **Settings > Environment Variables**로 이동합니다.
2. 다음 환경 변수를 등록합니다:
   - `ADMIN_USERNAME`: `admin`
   - `ADMIN_PASSWORD`: `123jesus`
   - `SECRET_KEY`: 임의의 긴 보안 문자열
   - `GCP_SERVICE_ACCOUNT_JSON`: `service_account_key.json` 파일의 전체 내용(JSON 문자열 원본)을 그대로 복사하여 값으로 붙여넣습니다.

---

## 📁 디렉토리 구조

```text
d:\antigravityhyunstts/
├── api/
│   └── index.py            # Flask 백엔드 및 Vercel 서버리스 진입점
├── app.py                  # 로컬 실행용 진입점
├── public/                 # 화이트 모드 프론트엔드
│   ├── index.html          # 메인 TTS 대시보드
│   ├── login.html          # 관리자 로그인 페이지
│   ├── css/
│   │   ├── style.css       # 화이트 모드 메인 스타일
│   │   └── login.css       # 로그인 페이지 스타일
│   └── js/
│       ├── app.js          # TTS 요청 및 오디오/다운로드 처리
│       └── login.js        # 로그인 폼 및 인증 상태 관리
├── requirements.txt        # 의존성 패키지
├── vercel.json             # Vercel 라우팅 설정
├── .env.example            # 환경변수 예시
├── .gitignore              # 보안 제외 목록
└── README.md               # 문서
```
