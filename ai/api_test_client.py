# api_test_client.py - FastAPI 테스트 클라이언트

import requests
import base64
from pathlib import Path

# =====================
# API 서버 URL
# =====================
API_URL = "http://localhost:8000"

# =====================
# 1. 파일 경로로 테스트
# =====================
def test_with_path(image_path: str):
    """파일 경로로 API 테스트"""
    print(f"\n🧪 파일 경로 테스트: {image_path}")
    
    response = requests.post(
        f"{API_URL}/predict/path",
        json={"image_path": image_path}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 성공!")
        print(f"결과: {result['result']}")
    else:
        print(f"❌ 실패: {response.status_code}")
        print(response.json())

# =====================
# 2. Base64로 테스트
# =====================
def test_with_base64(image_path: str):
    """Base64 인코딩으로 API 테스트"""
    print(f"\n🧪 Base64 테스트: {image_path}")
    
    # 이미지를 Base64로 인코딩
    with open(image_path, "rb") as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    response = requests.post(
        f"{API_URL}/predict/base64",
        json={"image_base64": image_base64}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 성공!")
        print(f"결과: {result['result']}")
    else:
        print(f"❌ 실패: {response.status_code}")
        print(response.json())

# =====================
# 3. 파일 업로드로 테스트
# =====================
def test_with_upload(image_path: str):
    """파일 업로드로 API 테스트"""
    print(f"\n🧪 파일 업로드 테스트: {image_path}")
    
    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}
        response = requests.post(
            f"{API_URL}/predict/upload",
            files=files
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 성공!")
        print(f"결과: {result['result']}")
    else:
        print(f"❌ 실패: {response.status_code}")
        print(response.json())

# =====================
# 4. 서버 상태 확인
# =====================
def check_server_status():
    """서버 상태 확인"""
    print("\n🔍 서버 상태 확인")
    
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 서버 실행 중")
            print(f"   서비스: {status['service']}")
            print(f"   상태: {status['status']}")
            print(f"   모델 로드됨: {status['model_loaded']}")
            return True
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        return False

# =====================
# 실행
# =====================
if __name__ == "__main__":
    # 서버 상태 확인
    if not check_server_status():
        print("\n먼저 API 서버를 실행하세요:")
        print("  python api.py")
        exit()
    
    # 테스트할 이미지 경로
    TEST_IMAGE = "./img/test.png"
    
    print("\n" + "="*60)
    print("📦 운송장 정보 추출 API 테스트")
    print("="*60)
    
    # 세 가지 방법으로 테스트
    test_with_path(TEST_IMAGE)
    test_with_base64(TEST_IMAGE)
    test_with_upload(TEST_IMAGE)
    
    print("\n" + "="*60)
    print("✅ 테스트 완료!")
    print("="*60)
