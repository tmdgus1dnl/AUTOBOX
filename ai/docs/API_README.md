# FastAPI 운송장 정보 추출 API

운송장 이미지에서 정보를 추출하는 FastAPI 기반 REST API입니다.

## 특징

- ✅ **서버 시작시 모델 사전 로딩** - 첫 요청부터 빠른 응답
- 🖼️ **3가지 입력 방식 지원**
  - 파일 경로 (로컬 파일 시스템)
  - Base64 인코딩된 이미지
  - 파일 업로드
- 🔧 **크로스 플랫폼** - Mac(CPU/MPS) 및 Windows(CUDA GPU) 모두 지원
- 📝 **자동 API 문서** - Swagger UI 제공

## 설치

필요한 패키지가 설치되어 있는지 확인:

```bash
pip install fastapi uvicorn python-multipart
```

## 서버 실행

```bash
python api.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

### 1. 서버 상태 확인

```bash
GET /
```

**응답 예시:**
```json
{
  "service": "운송장 정보 추출 API",
  "status": "running",
  "model_loaded": true
}
```

### 2. 파일 경로로 추론

```bash
POST /predict/path
```

**요청 본문:**
```json
{
  "image_path": "./img/test.png"
}
```

**응답 예시:**
```json
{
  "result": "{\"운송장번호\": \"75284412\", \"분류코드\": \"서울2\", ...}",
  "success": true,
  "message": "추출 성공"
}
```

### 3. Base64 이미지로 추론

```bash
POST /predict/base64
```

**요청 본문:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgA..."
}
```

### 4. 파일 업로드로 추론

```bash
POST /predict/upload
```

**Form Data:**
- `file`: 이미지 파일 (jpg, jpeg, png, webp, bmp)

## 사용 예시

### Python (requests)

```python
import requests
import base64

# 1. 파일 경로로 요청
response = requests.post(
    "http://localhost:8000/predict/path",
    json={"image_path": "./img/test.png"}
)
print(response.json())

# 2. Base64로 요청
with open("./img/test.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(
    "http://localhost:8000/predict/base64",
    json={"image_base64": image_base64}
)
print(response.json())

# 3. 파일 업로드로 요청
with open("./img/test.png", "rb") as f:
    files = {"file": ("test.png", f, "image/png")}
    response = requests.post(
        "http://localhost:8000/predict/upload",
        files=files
    )
print(response.json())
```

### cURL

```bash
# 파일 경로
curl -X POST "http://localhost:8000/predict/path" \
  -H "Content-Type: application/json" \
  -d '{"image_path": "./img/test.png"}'

# 파일 업로드
curl -X POST "http://localhost:8000/predict/upload" \
  -F "file=@./img/test.png"
```

### JavaScript (fetch)

```javascript
// Base64로 요청
const imageBase64 = "iVBORw0KGgoAAAANSUhEUgA...";

fetch("http://localhost:8000/predict/base64", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    image_base64: imageBase64
  })
})
.then(response => response.json())
.then(data => console.log(data));

// 파일 업로드
const formData = new FormData();
formData.append("file", fileInput.files[0]);

fetch("http://localhost:8000/predict/upload", {
  method: "POST",
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 테스트 클라이언트

제공된 테스트 클라이언트로 3가지 방식을 모두 테스트:

```bash
python api_test_client.py
```

## API 문서

서버 실행 후 자동 생성된 API 문서 확인:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 프로덕션 배포

프로덕션 환경에서는 더 많은 worker를 사용:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

또는 Gunicorn과 함께:

```bash
pip install gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 오류 처리

API는 다음과 같은 HTTP 상태 코드를 반환합니다:

- `200`: 성공
- `400`: 잘못된 요청 (지원하지 않는 파일 형식 등)
- `404`: 파일을 찾을 수 없음
- `500`: 서버 내부 오류
- `503`: 모델이 로드되지 않음
