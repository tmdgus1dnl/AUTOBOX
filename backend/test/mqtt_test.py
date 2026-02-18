#!/usr/bin/env python3
"""
MQTT 송수신 테스트 스크립트
EC2 서버에서 실행하여 라즈베리파이와 통신 테스트

사용법:
    python mqtt_test.py send     # 메시지 발행 (서버 → 라파)
    python mqtt_test.py receive  # 메시지 구독 (라파 → 서버)
    python mqtt_test.py both     # 발행 + 구독 동시
"""

import json
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

# ============================================
# 설정 (필요시 수정)
# ============================================
# 방법 1: 공개 테스트 브로커 (인터넷 필요, 가장 간단)
BROKER_HOST = "test.mosquitto.org"
BROKER_PORT = 1883

# 방법 2: EC2 로컬 (mosquitto 설치 필요)
# BROKER_HOST = "localhost"
# BROKER_PORT = 1883

# 토픽 (고유하게 설정 - 다른 사람과 겹치지 않게)
TOPIC_TO_RASPI = "server_msg"      # 서버 → 라즈베리파이
TOPIC_FROM_RASPI = "factory_msg"   # 라즈베리파이 → 서버

# 인증 (공개 브로커는 인증 없음)
USERNAME = None
PASSWORD = None


# ============================================
# 콜백 함수
# ============================================
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[✓] 브로커 연결 성공: {BROKER_HOST}:{BROKER_PORT}")
        # 연결 시 구독
        client.subscribe(f"{TOPIC_FROM_RASPI}/#")
        print(f"[✓] 구독 시작: {TOPIC_FROM_RASPI}/#")
    else:
        print(f"[✗] 연결 실패: {reason_code}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"[!] 연결 해제: {reason_code}")


def on_message(client, userdata, msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"\n[{timestamp}] 📥 수신")
        print(f"    토픽: {msg.topic}")
        print(f"    데이터: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    except:
        print(f"\n[{timestamp}] 📥 수신")
        print(f"    토픽: {msg.topic}")
        print(f"    데이터: {msg.payload.decode()}")


def on_publish(client, userdata, mid, reason_codes, properties):
    print(f"[✓] 발행 완료 (mid={mid})")


# ============================================
# 메인 함수
# ============================================
def create_client():
    """MQTT 클라이언트 생성"""
    client = mqtt.Client(
        client_id=f"test-{int(time.time())}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    # 인증 설정 (설정된 경우만)
    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    return client


def send_message(client, topic_suffix="cmd", message=None):
    """메시지 발행 (서버 → 라즈베리파이)"""
    topic = f"{TOPIC_TO_RASPI}/{topic_suffix}"
    
    if message is None:
        message = {
            "action": "test",
            "timestamp": datetime.now().isoformat(),
            "from": "ec2-server"
        }
    
    payload = json.dumps(message, ensure_ascii=False)
    result = client.publish(topic, payload)
    
    print(f"\n📤 발행")
    print(f"    토픽: {topic}")
    print(f"    데이터: {payload}")
    
    return result


def mode_send():
    """발행 모드"""
    print("\n" + "="*50)
    print("📤 발행 모드 (서버 → 라즈베리파이)")
    print("="*50)
    
    client = create_client()
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()
    
    time.sleep(1)  # 연결 대기
    
    print("\n명령어: [Enter]=테스트 발행, 'q'=종료")
    print("-"*50)
    
    try:
        while True:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'q':
                break
            
            # 기본 테스트 메시지 발행
            send_message(client, "cmd", {
                "action": "ping",
                "timestamp": datetime.now().isoformat(),
                "message": user_input if user_input else "Hello from EC2!"
            })
            
    except KeyboardInterrupt:
        pass
    
    client.loop_stop()
    client.disconnect()
    print("\n[종료]")


def mode_receive():
    """구독 모드"""
    print("\n" + "="*50)
    print("📥 구독 모드 (라즈베리파이 → 서버)")
    print("="*50)
    
    client = create_client()
    client.connect(BROKER_HOST, BROKER_PORT)
    
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
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()
    
    time.sleep(1)
    
    print("\n명령어: [Enter]=테스트 발행, 'q'=종료")
    print("수신된 메시지는 자동으로 표시됩니다.")
    print("-"*50)
    
    try:
        while True:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'q':
                break
            
            send_message(client, "cmd", {
                "action": "test",
                "timestamp": datetime.now().isoformat(),
                "message": user_input if user_input else "ping"
            })
            
    except KeyboardInterrupt:
        pass
    
    client.loop_stop()
    client.disconnect()
    print("\n[종료]")


def main():
    print("""
╔══════════════════════════════════════════════════╗
║         MQTT 송수신 테스트 (EC2 서버용)          ║
╠══════════════════════════════════════════════════╣
║  토픽 구조:                                      ║
║    서버 → 라파: server_msg/#                     ║
║    라파 → 서버: factory_msg/#                    ║
╚══════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python mqtt_test.py send     # 발행만")
        print("  python mqtt_test.py receive  # 구독만")
        print("  python mqtt_test.py both     # 양방향")
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
