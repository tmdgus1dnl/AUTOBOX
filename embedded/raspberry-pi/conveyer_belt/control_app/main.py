import paho.mqtt.client as mqtt
from conveyer_belt_control import ConveyerController
import ssl
import time
import json

conveyer = ConveyerController()

# --- 로컬 리스너 (젯슨 -> 라즈베리파이) ---
def on_local_message(client, userdata, msg):
    topic = msg.topic
    
    
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[LOCAL] {topic}: {payload}") # 예: {'cmd': 'PUSH', 'speed': 50}
    except json.JSONDecodeError:
        print(f"[LOCAL] JSON 형식이 아닙니다: {msg.payload}")
        return

    # 예: topic = "device/jetson-01/cmd" -> parts = ['device', 'jetson-01', 'cmd']
    parts = topic.split('/')
    
    
    if len(parts) < 3:
        return

    device_id = parts[1] #  'rc1',  'rc2'  ,  'rc3'   현재 프로젝트에선 1개만 존재.
    msg_type = parts[2]  #  'cmd',  'state',  'event'

    
    if msg_type == "cmd":
        # payload가 딕셔너리이므로 키값으로 접근
        if payload.get("cmd") == "PUSH":
            print(f" load to [{device_id}]")

            conveyer.servo_push()
            time.sleep(1)
            conveyer.servo_pull()
            
            event_data = {
                "event": "push_done",
                "device_id": device_id,
                "status": "success",
                "timestamp": time.time()
            }

            client_server.publish("server/factory/event", json.dumps(event_data))

    elif msg_type == "state":
        print(f"[{device_id}] 상태 업데이트: {payload}")
        # 서버로 그대로 토스 (중계)
        # payload에 device_id를 추가해서 보내주면 서버가 좋아함

        #payload['device_id'] = device_id 
        #client_server.publish("server/factory/state", json.dumps(payload))

    elif msg_type == "event":
        print(f"[{device_id}] 이벤트 발생: {payload}")
        # 서버로 중계
        #client_server.publish("server/factory/event", json.dumps(payload))


# --- 서버 리스너 (EC2 -> 라즈베리파이) ---
def on_server_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[SERVER 수신] {topic}: {payload}")
    except json.JSONDecodeError:
        return

    
    if topic == "server/factory/cmd":
        if payload.get("control") == "run":
            print("컨베이어 벨트 가동")
            conveyer.belt_run()


# --- 클라이언트 설정 및 실행 ---

# 1. 라즈베리파이 - 로컬 객체
client_local = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client_local.on_message = on_local_message
client_local.connect("mqtt-broker", 1883)
client_local.subscribe("device/+/+") # device/{아무거나}/{아무거나} 다 받음

# 2. 서버 - 라즈베리파이 객체

client_server = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

try:
    context = ssl.create_default_context()
    context.load_verify_locations("./ca.crt")
    client_server.tls_set_context(context)
    client_server.tls_insecure_set(True) 
except Exception as e:
    print(f"🚨 인증서 에러: {e}")
    exit()


def on_server_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("서버 MQTT 연결 성공")
        client.subscribe("server_msg/#")
    else:
        print(f"서버 MQTT 연결 실패: {reason_code}")

client_server.on_connect = on_server_connect
client_server.on_message = on_server_message
client_server.connect("43.201.254.235", 8883)



# 실행
client_local.loop_start()  
client_server.loop_start() 

try:
    while True:
        time.sleep(1) 
except KeyboardInterrupt:
    print("종료")
    conveyer.cleanup()
    client_local.loop_stop()
    client_server.loop_stop()
