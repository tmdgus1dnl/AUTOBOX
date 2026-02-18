/**
 * JavaScript에서 base64로 이미지를 FastAPI에 전송하는 예시
 */

// =====================
// 1. 파일 입력에서 base64로 변환하여 전송 (브라우저)
// =====================
async function sendImageFromFileInput(fileInputElement, apiUrl = "http://localhost:8000") {
    const file = fileInputElement.files[0];
    
    if (!file) {
        console.error("파일이 선택되지 않았습니다.");
        return;
    }
    
    // 파일을 base64로 변환
    const reader = new FileReader();
    
    return new Promise((resolve, reject) => {
        reader.onload = async function(e) {
            // data:image/png;base64,... 형식이므로 base64 부분만 추출
            const base64String = e.target.result.split(',')[1];
            
            try {
                // API 요청
                const response = await fetch(`${apiUrl}/predict/base64`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        image_base64: base64String
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    console.log('✅ 성공!', result);
                    resolve(result);
                } else {
                    console.error('❌ 오류:', result);
                    reject(result);
                }
            } catch (error) {
                console.error('❌ 네트워크 오류:', error);
                reject(error);
            }
        };
        
        reader.onerror = function(error) {
            console.error('파일 읽기 오류:', error);
            reject(error);
        };
        
        reader.readAsDataURL(file);
    });
}

// =====================
// 2. 이미 base64로 인코딩된 문자열 전송
// =====================
async function sendBase64String(imageBase64, apiUrl = "http://localhost:8000") {
    try {
        const response = await fetch(`${apiUrl}/predict/base64`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_base64: imageBase64
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('✅ 성공!', result);
            return result;
        } else {
            console.error('❌ 오류:', result);
            throw new Error(result.detail || 'API 오류');
        }
    } catch (error) {
        console.error('❌ 네트워크 오류:', error);
        throw error;
    }
}

// =====================
// 3. URL에서 이미지를 가져와서 base64로 변환 후 전송 (Node.js)
// =====================
async function sendImageFromUrl(imageUrl, apiUrl = "http://localhost:8000") {
    // Node.js 환경에서만 작동
    const axios = require('axios');
    
    try {
        // 이미지 다운로드
        const imageResponse = await axios.get(imageUrl, {
            responseType: 'arraybuffer'
        });
        
        // base64로 변환
        const imageBase64 = Buffer.from(imageResponse.data, 'binary').toString('base64');
        
        // API 요청
        const response = await axios.post(`${apiUrl}/predict/base64`, {
            image_base64: imageBase64
        });
        
        console.log('✅ 성공!', response.data);
        return response.data;
    } catch (error) {
        console.error('❌ 오류:', error.message);
        throw error;
    }
}

// =====================
// 4. HTML 예시 (브라우저)
// =====================
/*
<!DOCTYPE html>
<html>
<head>
    <title>운송장 OCR 테스트</title>
</head>
<body>
    <h1>운송장 이미지 업로드</h1>
    <input type="file" id="imageInput" accept="image/*">
    <button onclick="processImage()">분석하기</button>
    <div id="result"></div>
    
    <script>
        async function processImage() {
            const fileInput = document.getElementById('imageInput');
            const resultDiv = document.getElementById('result');
            
            try {
                resultDiv.textContent = '분석 중...';
                
                const result = await sendImageFromFileInput(
                    fileInput, 
                    'http://localhost:8000'
                );
                
                resultDiv.innerHTML = `
                    <h3>결과:</h3>
                    <pre>${JSON.stringify(JSON.parse(result.result), null, 2)}</pre>
                `;
            } catch (error) {
                resultDiv.textContent = '오류: ' + error.message;
            }
        }
        
        // sendImageFromFileInput 함수를 여기에 포함
    </script>
</body>
</html>
*/

// =====================
// 사용 예시
// =====================

// 브라우저에서:
// const fileInput = document.getElementById('myFileInput');
// sendImageFromFileInput(fileInput, 'http://your-server-ip:8000');

// Node.js에서:
// sendImageFromUrl('https://example.com/image.png', 'http://localhost:8000');
