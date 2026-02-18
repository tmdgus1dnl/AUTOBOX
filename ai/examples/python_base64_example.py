"""
Python에서 base64로 이미지를 FastAPI에 전송하는 예시
"""

import requests
import base64

# =====================
# 1. 로컬 파일을 base64로 인코딩해서 전송
# =====================
def send_image_as_base64(image_path: str, api_url: str = "http://localhost:8000"):
    """이미지 파일을 base64로 인코딩하여 API에 전송"""
    
    # 이미지 파일을 읽어서 base64로 인코딩
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # API 요청
    response = requests.post(
        f"{api_url}/predict/base64",
        json={"image_base64": image_base64},
        headers={"Content-Type": "application/json"}
    )
    
    # 결과 처리
    if response.status_code == 200:
        result = response.json()
        print("✅ 성공!")
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Result: {result['result']}")
        return result
    else:
        print(f"❌ 오류: {response.status_code}")
        print(response.text)
        return None

# =====================
# 2. 이미 base64로 인코딩된 문자열이 있는 경우
# =====================
def send_base64_string(image_base64: str, api_url: str = "http://localhost:8000"):
    """이미 base64로 인코딩된 문자열을 API에 전송"""
    
    response = requests.post(
        f"{api_url}/predict/base64",
        json={"image_base64": image_base64},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

# =====================
# 3. 웹에서 다운로드한 이미지를 바로 전송
# =====================
def send_image_from_url(image_url: str, api_url: str = "http://localhost:8000"):
    """URL에서 이미지를 다운로드하여 base64로 변환 후 전송"""
    
    # 이미지 다운로드
    image_response = requests.get(image_url)
    if image_response.status_code != 200:
        raise Exception(f"이미지 다운로드 실패: {image_url}")
    
    # base64로 인코딩
    image_base64 = base64.b64encode(image_response.content).decode('utf-8')
    
    # API 요청
    response = requests.post(
        f"{api_url}/predict/base64",
        json={"image_base64": image_base64},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

# =====================
# 사용 예시
# =====================
if __name__ == "__main__":
    # API 서버 URL (외부 서버라면 해당 IP:Port로 변경)
    API_URL = "http://localhost:8000"
    
    print("📦 Base64 이미지 전송 예시\n")
    
    # 예시 1: 로컬 파일 전송
    print("1️⃣ 로컬 파일 전송")
    result = send_image_as_base64("./img/test.png", API_URL)
    
    # 예시 2: 이미 인코딩된 base64 문자열 전송
    # (실제로는 다른 시스템이나 데이터베이스에서 받은 base64 문자열)
    print("\n2️⃣ Base64 문자열 직접 전송")
    with open("./img/test.png", "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode('utf-8')
    result = send_base64_string(encoded_string, API_URL)
    print(f"결과: {result['result']}")
