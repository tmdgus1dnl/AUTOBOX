import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Base64;
import org.json.JSONObject;

/**
 * Java에서 base64로 이미지를 FastAPI에 전송하는 예시
 * 
 * 필요한 라이브러리:
 * - org.json (JSON 처리용)
 *   Maven: <dependency>
 *            <groupId>org.json</groupId>
 *            <artifactId>json</artifactId>
 *            <version>20230227</version>
 *          </dependency>
 */
public class Base64ImageSender {
    
    private static final String API_URL = "http://localhost:8000/predict/base64";
    
    /**
     * 1. 파일에서 이미지를 읽어 base64로 변환하여 전송
     */
    public static JSONObject sendImageFile(String imagePath) throws IOException {
        // 이미지 파일 읽기
        byte[] imageBytes = Files.readAllBytes(Paths.get(imagePath));
        
        // base64로 인코딩
        String imageBase64 = Base64.getEncoder().encodeToString(imageBytes);
        
        // API 요청
        return sendBase64String(imageBase64);
    }
    
    /**
     * 2. base64 문자열을 API에 전송
     */
    public static JSONObject sendBase64String(String imageBase64) throws IOException {
        // URL 연결 설정
        URL url = new URL(API_URL);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);
        
        // JSON 요청 본문 생성
        JSONObject requestBody = new JSONObject();
        requestBody.put("image_base64", imageBase64);
        
        // 요청 전송
        try (OutputStream os = conn.getOutputStream()) {
            byte[] input = requestBody.toString().getBytes("utf-8");
            os.write(input, 0, input.length);
        }
        
        // 응답 읽기
        int responseCode = conn.getResponseCode();
        
        BufferedReader br;
        if (responseCode == HttpURLConnection.HTTP_OK) {
            br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "utf-8"));
        } else {
            br = new BufferedReader(new InputStreamReader(conn.getErrorStream(), "utf-8"));
        }
        
        StringBuilder response = new StringBuilder();
        String responseLine;
        while ((responseLine = br.readLine()) != null) {
            response.append(responseLine.trim());
        }
        br.close();
        
        // JSON 파싱
        JSONObject jsonResponse = new JSONObject(response.toString());
        
        if (responseCode == HttpURLConnection.HTTP_OK) {
            System.out.println("✅ 성공!");
            System.out.println("결과: " + jsonResponse.getString("result"));
        } else {
            System.err.println("❌ 오류: " + responseCode);
            System.err.println(jsonResponse.toString());
        }
        
        return jsonResponse;
    }
    
    /**
     * 사용 예시
     */
    public static void main(String[] args) {
        try {
            System.out.println("📦 Base64 이미지 전송 예시 (Java)\n");
            
            // 이미지 파일 전송
            String imagePath = "./img/test.png";
            JSONObject result = sendImageFile(imagePath);
            
            // 결과 출력
            System.out.println("\n결과:");
            System.out.println("Success: " + result.getBoolean("success"));
            System.out.println("Message: " + result.getString("message"));
            System.out.println("Result: " + result.getString("result"));
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}

/**
 * Spring Boot를 사용하는 경우:
 */
/*
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import java.util.Base64;
import java.nio.file.Files;
import java.nio.file.Paths;

@Service
public class OcrService {
    
    private static final String API_URL = "http://localhost:8000/predict/base64";
    private final RestTemplate restTemplate = new RestTemplate();
    
    public String extractInfo(String imagePath) throws IOException {
        // 이미지를 base64로 변환
        byte[] imageBytes = Files.readAllBytes(Paths.get(imagePath));
        String imageBase64 = Base64.getEncoder().encodeToString(imageBytes);
        
        // 요청 본문 생성
        Map<String, String> request = new HashMap<>();
        request.put("image_base64", imageBase64);
        
        // HTTP 헤더 설정
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        // HTTP 엔티티 생성
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(request, headers);
        
        // API 호출
        ResponseEntity<Map> response = restTemplate.postForEntity(
            API_URL, 
            entity, 
            Map.class
        );
        
        if (response.getStatusCode() == HttpStatus.OK) {
            Map<String, Object> body = response.getBody();
            return (String) body.get("result");
        } else {
            throw new RuntimeException("API 호출 실패: " + response.getStatusCode());
        }
    }
}
*/
