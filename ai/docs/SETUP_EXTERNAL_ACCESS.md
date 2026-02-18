# 🌐 외부 IP에서 FastAPI 서버 접근 설정 가이드

이 가이드는 외부 네트워크에서 FastAPI 서버에 접근할 수 있도록 설정하는 방법을 설명합니다.

## 📋 준비 사항

### 1. 패키지 설치

먼저 필요한 패키지를 설치하세요:

```bash
pip install python-dotenv
```

또는 전체 requirements.txt 설치:

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일이 이미 생성되어 있습니다. 필요에 따라 수정하세요:

```bash
# .env 파일 내용
HOST=0.0.0.0          # 모든 네트워크 인터페이스에서 접근 허용
PORT=8000             # 포트 번호
ADAPTER_PATH=./model/qwen2_vl_finetuned_ver2  # 모델 경로
ALLOWED_ORIGINS=*     # CORS 허용 도메인 (모든 도메인 허용)
```

## 🚀 서버 실행

```bash
python api.py
```

서버가 시작되면 다음과 같은 메시지가 표시됩니다:
```
🚀 서버 시작: http://0.0.0.0:8000
📝 API 문서: http://0.0.0.0:8000/docs
🔧 모델 경로: ./model/qwen2_vl_finetuned_ver2
```

## 🔧 외부 접근 설정

### 1. 서버 IP 확인

**Mac에서 IP 확인:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**또는:**
```bash
ipconfig getifaddr en0  # Wi-Fi
ipconfig getifaddr en1  # 이더넷
```

예시 출력: `192.168.1.100`

### 2. 방화벽 설정 (Mac)

Mac은 기본적으로 방화벽이 꺼져있지만, 켜져있다면 포트를 허용해야 합니다:

```bash
# 방화벽 상태 확인
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 방화벽이 켜져있다면, Python 허용
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/bin/python3
```

또는 시스템 환경설정 → 보안 및 개인 정보 보호 → 방화벽 → 방화벽 옵션에서 Python 허용

### 3. 외부에서 접근 테스트

다른 컴퓨터나 스마트폰에서:

```bash
# 서버 상태 확인
curl http://192.168.1.100:8000/

# API 테스트 (다른 컴퓨터에서)
curl -X POST "http://192.168.1.100:8000/predict/path" \
  -H "Content-Type: application/json" \
  -d '{"image_path": "./img/test.png"}'
```

또는 브라우저에서:
```
http://192.168.1.100:8000/docs
```

## 🔒 보안 설정

### CORS 특정 도메인만 허용

프로덕션 환경에서는 모든 도메인(`*`)을 허용하는 대신 특정 도메인만 허용하세요:

`.env` 파일 수정:
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://192.168.1.100:3000,https://yourdomain.com
```

### 방화벽 규칙 (프로덕션)

프로덕션 환경에서는 신뢰할 수 있는 IP만 허용:

```bash
# Mac에서 pf를 사용한 방화벽 설정 예시
# /etc/pf.conf 편집
sudo vim /etc/pf.conf

# 특정 IP만 8000 포트 허용 추가
# pass in proto tcp from 192.168.1.0/24 to any port 8000
```

## 📱 클라이언트 사용 예시

### Python
```python
import requests
import base64

API_URL = "http://192.168.1.100:8000"  # 서버 IP로 변경

with open("image.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(
    f"{API_URL}/predict/base64",
    json={"image_base64": image_base64}
)

print(response.json())
```

### JavaScript (웹 브라우저)
```javascript
const API_URL = "http://192.168.1.100:8000";  // 서버 IP로 변경

fetch(`${API_URL}/predict/base64`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({image_base64: base64String})
})
.then(res => res.json())
.then(data => console.log(data));
```

## 🌐 공인 IP로 외부 인터넷에서 접근 (고급)

### 1. 포트 포워딩 설정

라우터 관리 페이지에서:
1. 포트 포워딩 설정 메뉴 접근
2. 외부 포트: 8000 → 내부 IP: 192.168.1.100, 포트: 8000
3. 프로토콜: TCP

### 2. 공인 IP 확인

```bash
curl ifconfig.me
```

### 3. 외부에서 접근

공인 IP가 `203.0.113.1`이라면:
```
http://203.0.113.1:8000
```

> ⚠️ **주의:** 공인 IP로 서비스 배포 시 반드시 HTTPS 및 인증 추가 필요!

## 🐳 Docker로 배포 (선택사항)

Docker를 사용하면 더 쉽게 배포할 수 있습니다:

```dockerfile
FROM python:3.10

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "api.py"]
```

실행:
```bash
docker build -t ocr-api .
docker run -p 8000:8000 --env-file .env ocr-api
```

## 🔍 문제 해결

### 연결 거부됨 (Connection Refused)
- 방화벽 확인
- 서버가 실행 중인지 확인
- IP 주소가 올바른지 확인

### CORS 오류
- `.env`의 `ALLOWED_ORIGINS` 확인
- 클라이언트 도메인이 허용 목록에 있는지 확인

### 느린 응답
- 모델이 CPU에서 실행 중인지 확인 (GPU 사용 권장)
- 네트워크 대역폭 확인
- 이미지 크기 최적화

## 📚 추가 문서

- [API 사용 가이드](./API_README.md)
- [Base64 전송 예시](./examples/README.md)
