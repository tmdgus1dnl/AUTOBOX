#!/usr/bin/env python3
"""
라즈베리파이용 MQTT 테스트 스크립트
라즈베리파이에서 실행하여 EC2 서버와 통신 테스트

사용법:
    python raspi_test.py send     # 메시지 발행 (라파 → 서버)
    python raspi_test.py receive  # 메시지 구독 (서버 → 라파)
    python raspi_test.py both     # 발행 + 구독 동시
"""

import json
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

# ============================================
# 설정 (⚠️ 필요시 수정)
# ============================================
# 공개 테스트 브로커 (인터넷만 되면 바로 테스트 가능!)
BROKER_HOST = "test.mosquitto.org"
BROKER_PORT = 1883
USE_TLS = False  # 공개 브로커는 TLS 없이

# EC2 직접 연결 시 (나중에 사용)
# BROKER_HOST = "43.201.254.235"
# BROKER_PORT = 8883
# USE_TLS = True

# 인증서 경로 (TLS 사용 시)
CA_CERT = "/home/pi/autobox/certs/ca.crt"

# 토픽 (고유하게 설정)
TOPIC_TO_SERVER = "ssafy/a403/factory_msg"    # 라즈베리파이 → 서버
TOPIC_FROM_SERVER = "ssafy/a403/server_msg"   # 서버 → 라즈베리파이

# 인증 (공개 브로커는 인증 없음)
USERNAME = None
PASSWORD = None


# ============================================
# 콜백 함수
# ============================================
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[✓] EC2 브로커 연결 성공: {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe(f"{TOPIC_FROM_SERVER}/#")
        print(f"[✓] 구독 시작: {TOPIC_FROM_SERVER}/#")
    else:
        print(f"[✗] 연결 실패: {reason_code}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"[!] 연결 해제: {reason_code}")


def on_message(client, userdata, msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"\n[{timestamp}] 📥 EC2에서 수신")
        print(f"    토픽: {msg.topic}")
        print(f"    데이터: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    except:
        print(f"\n[{timestamp}] 📥 EC2에서 수신")
        print(f"    토픽: {msg.topic}")
        print(f"    데이터: {msg.payload.decode()}")


def on_publish(client, userdata, mid, reason_codes, properties):
    print(f"[✓] EC2로 발행 완료 (mid={mid})")


# ============================================
# 메인 함수
# ============================================
def create_client():
    """MQTT 클라이언트 생성"""
    client = mqtt.Client(
        client_id=f"raspi-{int(time.time())}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    
    # TLS 설정 (USE_TLS가 True일 때만)
    if USE_TLS:
        client.tls_set(ca_certs=CA_CERT)
        client.tls_insecure_set(True)
    
    # 인증 설정 (설정된 경우만)
    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    
    return client


def send_message(client, topic_suffix="state", message=None):
    """메시지 발행 (라즈베리파이 → 서버)"""
    topic = f"{TOPIC_TO_SERVER}/{topic_suffix}"
    
    if message is None:
        message = {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "from": "raspberry-pi"
        }
    
    payload = json.dumps(message, ensure_ascii=False)
    result = client.publish(topic, payload)
    
    print(f"\n📤 EC2로 발행")
    print(f"    토픽: {topic}")
    print(f"    데이터: {payload}")
    
    return result


def mode_send():
    """발행 모드"""
    print("\n" + "="*50)
    print("📤 발행 모드 (라즈베리파이 → EC2)")
    print("="*50)
    
    client = create_client()
    
    try:
        client.connect(BROKER_HOST, BROKER_PORT)
    except Exception as e:
        print(f"[✗] 연결 실패: {e}")
        print("\n확인 사항:")
        print("  1. EC2 IP가 올바른지 확인")
        print("  2. 8883 포트가 열려있는지 확인")
        print("  3. ca.crt 파일 경로 확인")
        return
    
    client.loop_start()
    time.sleep(2)
    
    print("\n명령어: [Enter]=테스트 발행, 'q'=종료")
    print("-"*50)
    
    try:
        while True:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'q':
                break
            
            send_message(client, "state", {
                "status": "active",
                "sensor": "test",
                "value": 123,
                "timestamp": datetime.now().isoformat(),
                "message": user_input if user_input else "Hello from RasPi!"
            })
            
    except KeyboardInterrupt:
        pass
    
    client.loop_stop()
    client.disconnect()
    print("\n[종료]")


def mode_receive():
    """구독 모드"""
    print("\n" + "="*50)
    print("📥 구독 모드 (EC2 → 라즈베리파이)")
    print("="*50)
    
    client = create_client()
    
    try:
        client.connect(BROKER_HOST, BROKER_PORT)
    except Exception as e:
        print(f"[✗] 연결 실패: {e}")
        return
    
    print("\nCtrl+C로 종료")
    print("-"*50)
    
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass
    
    client.disconnect()
    print("\n[종료]")


def mode_both():
    """발행 + 구독 동시"""
    print("\n" + "="*50)
    print("📤📥 양방향 모드")
    print("="*50)
    
    client = create_client()
    
    try:
        client.connect(BROKER_HOST, BROKER_PORT)
    except Exception as e:
        print(f"[✗] 연결 실패: {e}")
        return
    
    client.loop_start()
    time.sleep(2)
    
    print("\n명령어: [Enter]=테스트 발행, 'q'=종료")
    print("EC2에서 온 메시지는 자동으로 표시됩니다.")
    print("-"*50)
    
    try:
        while True:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'q':
                break
            
            send_message(client, "state", {
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "message": user_input if user_input else "ping from raspi"
            })
            
    except KeyboardInterrupt:
        pass
    
    client.loop_stop()
    client.disconnect()
    print("\n[종료]")


def main():
    print("""
╔══════════════════════════════════════════════════╗
║       MQTT 송수신 테스트 (라즈베리파이용)        ║
╠══════════════════════════════════════════════════╣
║  토픽 구조:                                      ║
║    라파 → 서버: factory_msg/#                    ║
║    서버 → 라파: server_msg/#                     ║
╚══════════════════════════════════════════════════╝
    """)
    
    # 설정 확인
    if BROKER_HOST == "YOUR_EC2_IP":
        print("⚠️  EC2 IP를 설정해주세요!")
        print("   raspi_test.py 파일 상단의 BROKER_HOST 수정")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python raspi_test.py send     # 발행만")
        print("  python raspi_test.py receive  # 구독만")
        print("  python raspi_test.py both     # 양방향")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "send":
        mode_send()
    elif mode == "receive":
        mode_receive()
    elif mode == "both":
        mode_both()
    else:
        print(f"알 수 없는 모드: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
