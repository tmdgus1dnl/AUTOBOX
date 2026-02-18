#!/usr/bin/env python3
"""
서버 IP 주소 확인 및 테스트 스크립트
"""

import socket
import subprocess
import platform

def get_local_ip():
    """로컬 네트워크 IP 주소 가져오기"""
    try:
        # 가장 간단한 방법: 외부 연결 시도 (실제로 연결하지 않음)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def get_all_ips():
    """모든 네트워크 인터페이스의 IP 주소 가져오기"""
    hostname = socket.gethostname()
    try:
        ips = socket.getaddrinfo(hostname, None)
        # IPv4 주소만 필터링
        ipv4_addresses = [ip[4][0] for ip in ips if ip[0] == socket.AF_INET and ip[4][0] != '127.0.0.1']
        return list(set(ipv4_addresses))  # 중복 제거
    except Exception:
        return []

def get_public_ip():
    """공인 IP 주소 가져오기 (인터넷 연결 필요)"""
    try:
        import requests
        response = requests.get('https://api.ipify.org', timeout=3)
        return response.text
    except:
        return None

def check_port_open(port=8000):
    """포트가 사용 중인지 확인"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', port))
        s.close()
        return result == 0
    except:
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🌐 FastAPI 서버 네트워크 정보")
    print("=" * 60)
    
    # 호스트 이름
    hostname = socket.gethostname()
    print(f"\n📛 호스트 이름: {hostname}")
    
    # 로컬 IP
    local_ip = get_local_ip()
    if local_ip:
        print(f"🏠 로컬 네트워크 IP: {local_ip}")
        print(f"   → 같은 네트워크의 다른 기기에서 접근: http://{local_ip}:8000")
    
    # 모든 IP 주소
    all_ips = get_all_ips()
    if all_ips and len(all_ips) > 1:
        print(f"\n📡 사용 가능한 모든 IP 주소:")
        for ip in all_ips:
            print(f"   - {ip}")
    
    # 공인 IP (선택사항)
    print(f"\n🌍 공인 IP 확인 중...")
    public_ip = get_public_ip()
    if public_ip:
        print(f"   공인 IP: {public_ip}")
        print(f"   ⚠️  포트 포워딩 설정 후 외부 접근 가능: http://{public_ip}:8000")
    else:
        print(f"   공인 IP를 가져올 수 없습니다 (인터넷 연결 확인)")
    
    # 포트 상태 확인
    print(f"\n🔍 포트 8000 상태 확인:")
    if check_port_open(8000):
        print(f"   ✅ 포트 8000이 열려있습니다 (서버 실행 중)")
    else:
        print(f"   ⚠️  포트 8000이 닫혀있습니다 (서버가 실행 중이 아님)")
    
    # 접속 URL 안내
    print(f"\n📋 접속 URL:")
    print(f"   로컬: http://localhost:8000")
    if local_ip:
        print(f"   네트워크: http://{local_ip}:8000")
        print(f"   API 문서: http://{local_ip}:8000/docs")
    
    # 방화벽 확인 (Mac)
    if platform.system() == "Darwin":  # macOS
        print(f"\n🔒 방화벽 상태 (Mac):")
        try:
            result = subprocess.run(
                ["sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                capture_output=True,
                text=True,
                timeout=3
            )
            print(f"   {result.stdout.strip()}")
        except:
            print(f"   방화벽 상태를 확인할 수 없습니다")
    
    print("\n" + "=" * 60)
    print("✅ 확인 완료!")
    print("=" * 60)
    print("\n💡 팁:")
    print("   1. 서버 실행: python api.py")
    print("   2. 다른 기기에서 테스트: curl http://{local_ip}:8000/")
    print("   3. 자세한 설정: SETUP_EXTERNAL_ACCESS.md 참고")
    print()
