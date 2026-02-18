# 외부에서 Base64 이미지를 FastAPI로 전송하기

외부 시스템에서 base64로 인코딩된 이미지를 FastAPI OCR 서버에 전송하는 방법입니다.

## 🚀 빠른 시작

**API 엔드포인트:**
```
POST http://your-server-ip:8000/predict/base64
```

**요청 형식:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgA..."
}
```

**응답 형식:**
```json
{
  "result": "{\"운송장번호\": \"75284412\", ...}",
  "success": true,
  "message": "추출 성공"
}
```

## 📋 언어별 예시

### Python

```python
import requests
import base64

# 이미지를 base64로 인코딩
with open("image.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# API 요청
response = requests.post(
    "http://localhost:8000/predict/base64",
    json={"image_base64": image_base64}
)

result = response.json()
print(result["result"])
```

**전체 예시:** [`python_base64_example.py`](./python_base64_example.py)

### JavaScript (브라우저)

```javascript
// 파일 입력에서 이미지 읽기
const fileInput = document.getElementById('myInput');
const file = fileInput.files[0];

const reader = new FileReader();
reader.onload = async function(e) {
    const base64String = e.target.result.split(',')[1];
    
    const response = await fetch('http://localhost:8000/predict/base64', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image_base64: base64String})
    });
    
    const result = await response.json();
    console.log(result.result);
};

reader.readAsDataURL(file);
```

**전체 예시:** [`javascript_base64_example.js`](./javascript_base64_example.js)

### cURL (Linux/Mac)

```bash
# 이미지를 base64로 인코딩하여 전송
curl -X POST "http://localhost:8000/predict/base64" \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\": \"$(base64 -i image.png)\"}"
```

**전체 예시:** [`curl_base64_example.sh`](./curl_base64_example.sh)

### Java

```java
import java.util.Base64;
import java.nio.file.Files;
import java.nio.file.Paths;
import org.json.JSONObject;

// 이미지를 base64로 변환
byte[] imageBytes = Files.readAllBytes(Paths.get("image.png"));
String imageBase64 = Base64.getEncoder().encodeToString(imageBytes);

// JSON 요청 생성
JSONObject requestBody = new JSONObject();
requestBody.put("image_base64", imageBase64);

// HTTP 요청 (코드 생략)
```

**전체 예시:** [`java_base64_example.java`](./java_base64_example.java)

### Spring Boot

```java
@Service
public class OcrService {
    private final RestTemplate restTemplate = new RestTemplate();
    
    public String extractInfo(String imagePath) throws IOException {
        byte[] imageBytes = Files.readAllBytes(Paths.get(imagePath));
        String imageBase64 = Base64.getEncoder().encodeToString(imageBytes);
        
        Map<String, String> request = Map.of("image_base64", imageBase64);
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(request);
        
        ResponseEntity<Map> response = restTemplate.postForEntity(
            "http://localhost:8000/predict/base64",
            entity,
            Map.class
        );
        
        return (String) response.getBody().get("result");
    }
}
```

## 📝 핵심 포인트

### 1. **Base64 인코딩**
이미지 파일을 base64 문자열로 변환:
- Python: `base64.b64encode(image_bytes).decode('utf-8')`
- JavaScript: `btoa()` 또는 `FileReader.readAsDataURL()`
- Java: `Base64.getEncoder().encodeToString()`

### 2. **HTTP 요청**
- **Method:** POST
- **URL:** `http://your-server-ip:8000/predict/base64`
- **Headers:** `Content-Type: application/json`
- **Body:** `{"image_base64": "..."}`

### 3. **외부 접근 설정**

**서버가 다른 컴퓨터/네트워크에 있는 경우:**

1. API 서버를 외부에서 접근 가능하게 실행:
   ```bash
   # api.py에서 이미 0.0.0.0으로 설정되어 있음
   python api.py
   ```

2. 방화벽 포트 열기:
   ```bash
   # Linux (ufw)
   sudo ufw allow 8000
   
   # Windows 방화벽
   # 제어판 -> Windows Defender 방화벽 -> 인바운드 규칙 -> 8000 포트 추가
   ```

3. 클라이언트에서 서버 IP 사용:
   ```python
   API_URL = "http://192.168.1.100:8000"  # 서버의 실제 IP
   ```

### 4. **이미지 크기 제한**

Base64로 인코딩하면 원본 크기의 약 1.33배가 됩니다.
큰 이미지의 경우:
- API에 크기 제한 추가 고려
- 또는 `/predict/upload` 엔드포인트 사용 (파일 업로드 방식)

## 🧪 테스트

1. **API 서버 실행:**
   ```bash
   python api.py
   ```

2. **예시 코드 실행:**
   ```bash
   # Python
   python examples/python_base64_example.py
   
   # Bash
   bash examples/curl_base64_example.sh
   
   # Java
   javac examples/java_base64_example.java
   java Base64ImageSender
   ```

## 🔒 보안 고려사항

프로덕션 환경에서는:
- HTTPS 사용 (SSL/TLS)
- API 키 또는 JWT 토큰으로 인증
- Rate limiting 적용
- 이미지 크기 검증

## 📚 추가 정보

- **전체 API 문서:** [`API_README.md`](../API_README.md)
- **API 자동 문서:** http://localhost:8000/docs (서버 실행 후)
