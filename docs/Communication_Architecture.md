# AutoBox 통신 아키텍처

## 개요

AutoBox 시스템은 **Edge-Cloud 하이브리드 아키텍처**를 사용하여 현장(라즈베리파이 + 오린나노)과 클라우드(EC2) 간의 안전한 양방향 통신을 지원합니다.

## 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           현장 (로컬 네트워크)                               │
│                                                                             │
│  ┌──────────────┐      로컬 MQTT       ┌───────────────────────────────┐   │
│  │  오린 나노   │ ◀───────────────────▶│        라즈베리파이           │   │
│  │ (자율주행차) │     localhost:1883   │                               │   │
│  └──────────────┘                      │  ┌─────────────────────────┐  │   │
│                                        │  │  로컬 Mosquitto 브로커  │  │   │
│                                        │  │      (Port 1883)        │  │   │
│                                        │  └───────────┬─────────────┘  │   │
│                                        │              │                │   │
│                                        │              ▼                │   │
│                                        │  ┌─────────────────────────┐  │   │
│                                        │  │     Bridge Module       │  │   │
│                                        │  │  (EC2로 메시지 전달)    │  │   │
│                                        │  └───────────┬─────────────┘  │   │
│                                        └──────────────┼────────────────┘   │
└───────────────────────────────────────────────────────┼─────────────────────┘
                                                        │
                                           TLS 8883 (Outbound 연결)
                                           ✓ NAT/방화벽 통과
                                           ✓ 포트포워딩 불필요
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EC2 (클라우드)                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   Mosquitto Broker (autobox-mqtt)                    │   │
│  │                                                                      │   │
│  │   Port 1883: 내부용 (Docker 네트워크, 비TLS)                         │   │
│  │   Port 8883: 외부용 (라즈베리파이 연결, TLS 암호화)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│  │   Backend   │  │  Frontend   │  │   MySQL     │                        │
│  │  (FastAPI)  │  │  (Vue.js)   │  │  (Azure)    │                        │
│  │   :8000     │  │    :80      │  │             │                        │
│  └─────────────┘  └─────────────┘  └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 아키텍처 특징

### Edge-Cloud 하이브리드 구조

| 계층 | 위치 | 역할 | 장점 |
|------|------|------|------|
| **Edge** | 라즈베리파이 | 로컬 브로커 + 브릿지 | 저지연 통신, 오프라인 동작 |
| **Cloud** | EC2 | 중앙 브로커 + 백엔드 | 데이터 수집, 모니터링, 분석 |

### 보안 기능

| 기능 | 설명 |
|------|------|
| **TLS 1.2/1.3 암호화** | 모든 외부 통신 암호화 (Port 8883) |
| **Username/Password 인증** | 등록된 클라이언트만 접속 허용 |
| **Topic ACL** | 클라이언트별 토픽 접근 권한 제어 |
| **Outbound 연결** | NAT/방화벽 환경에서도 연결 가능 |

---

## 통신 방식

### 1. 라즈베리파이 → EC2 (MQTT Bridge)

| 항목 | 설명 |
|------|------|
| **프로토콜** | MQTT over TLS |
| **방향** | 라즈베리파이 → EC2 (Outbound) |
| **포트** | 8883 (TLS) |
| **용도** | 센서 데이터, 디바이스 상태, 알림 전송 |

**자동 전달되는 토픽:**
- `autobox/sensor/#` - 센서 데이터
- `autobox/device/#` - 디바이스 상태
- `autobox/alert/#` - 알림
- `autobox/camera/#` - 카메라 감지

### 2. EC2 → 라즈베리파이 (MQTT Command)

| 항목 | 설명 |
|------|------|
| **프로토콜** | MQTT over TLS |
| **방향** | EC2 → 라즈베리파이 |
| **포트** | 8883 (TLS) |
| **용도** | 제어 명령, 설정 변경 |

**명령 토픽:**
- `autobox/command/#` - 제어 명령

### 3. 오린나노 ↔ 라즈베리파이 (로컬 MQTT)

| 항목 | 설명 |
|------|------|
| **프로토콜** | MQTT (비암호화) |
| **방향** | 양방향 |
| **포트** | 1883 (localhost) |
| **용도** | 자율주행 제어, 센서 데이터 |

---

## 설치 및 설정

### EC2 서버 설정

#### 1. TLS 인증서 생성

```bash
cd mqtt/certs
chmod +x generate-certs.sh
./generate-certs.sh 43.201.254.235
```

#### 2. MQTT 비밀번호 설정

```bash
cd mqtt/config
chmod +x generate-passwd.sh
./generate-passwd.sh
```

#### 3. Docker 컨테이너 시작

```bash
docker-compose up -d
```

#### 4. EC2 보안그룹 설정

| 포트 | 프로토콜 | 소스 | 용도 |
|------|----------|------|------|
| 80 | TCP | 0.0.0.0/0 | Frontend |
| 8000 | TCP | 0.0.0.0/0 | Backend API |
| **8883** | TCP | 0.0.0.0/0 | **MQTT TLS** |

### 라즈베리파이 설정

#### 1. Mosquitto 설치

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
```

#### 2. 인증서 복사

```bash
# EC2에서 라즈베리파이로 복사
scp mqtt/certs/ca.crt pi@<RPI_IP>:/home/pi/autobox/certs/
scp mqtt/certs/client.crt pi@<RPI_IP>:/home/pi/autobox/certs/
scp mqtt/certs/client.key pi@<RPI_IP>:/home/pi/autobox/certs/
```

#### 3. 브릿지 설정

```bash
# 설정 파일 복사
sudo cp embedded/raspberry-pi/mosquitto-bridge.conf /etc/mosquitto/conf.d/bridge.conf

# EC2 IP 및 비밀번호 수정
sudo nano /etc/mosquitto/conf.d/bridge.conf

# 재시작
sudo systemctl restart mosquitto
```

---

## MQTT Topic 구조

```
autobox/
├── sensor/
│   ├── data          # 센서 데이터 (라즈베리파이 → EC2)
│   └── status        # 센서 상태
├── device/
│   ├── status        # 디바이스 상태 (라즈베리파이 → EC2)
│   └── heartbeat     # 연결 유지 신호
├── alert/
│   └── notification  # 알림 이벤트 (라즈베리파이 → EC2)
├── camera/
│   └── detection     # 카메라 감지 (라즈베리파이 → EC2)
├── command/
│   └── #             # 제어 명령 (EC2 → 라즈베리파이)
└── bridge/
    └── status        # 브릿지 연결 상태
```

---

## 데이터 흐름

```
오린나노                라즈베리파이              EC2
   │                        │                      │
   │  센서 데이터           │                      │
   │  (autobox/sensor/*)    │                      │
   │ ─────────────────────▶ │                      │
   │                        │  브릿지 자동 전달    │
   │                        │  (TLS 암호화)        │
   │                        │ ────────────────────▶│
   │                        │                      │  DB 저장
   │                        │                      │  WebSocket 전달
   │                        │                      │  대시보드 표시
   │                        │                      │
   │                        │     제어 명령        │
   │                        │  (autobox/command/*) │
   │                        │ ◀────────────────────│
   │   명령 수신            │                      │
   │ ◀───────────────────── │                      │
```

---

## 연결 테스트

### EC2 브로커 테스트

```bash
# 컨테이너 내부에서 구독
docker exec -it autobox-mqtt mosquitto_sub -h localhost -t "autobox/#" -v

# 다른 터미널에서 발행
docker exec -it autobox-mqtt mosquitto_pub -h localhost -t "autobox/test" -m "Hello"
```

### 라즈베리파이 브릿지 테스트

```bash
# 라즈베리파이에서 로컬 발행
mosquitto_pub -h localhost -t "autobox/sensor/data" -m '{"temp": 25.5}'

# EC2에서 수신 확인
docker exec -it autobox-mqtt mosquitto_sub -h localhost -t "autobox/#" -v
```

### TLS 연결 테스트

```bash
# 라즈베리파이에서 EC2로 직접 연결
mosquitto_sub -h EC2_IP -p 8883 \
  --cafile /home/pi/autobox/certs/ca.crt \
  -u raspberry-pi -P your_password \
  -t "autobox/#" -v
```

---

## 환경 변수

### EC2 (.env)

```env
# MQTT Broker (Docker internal)
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_TOPIC_PREFIX=autobox
MQTT_CLIENT_ID=autobox-backend
MQTT_USERNAME=backend
MQTT_PASSWORD=your_password
MQTT_ENABLED=true
```

### 라즈베리파이 (.env)

```env
# EC2 MQTT Broker (TLS)
EC2_BROKER_HOST=43.201.254.235
EC2_BROKER_PORT=8883
MQTT_USERNAME=raspberry-pi
MQTT_PASSWORD=your_password

# TLS Certificates
CA_CERT_PATH=/home/pi/autobox/certs/ca.crt

# Local Settings
DEVICE_ID=rpi-001
```

---

## 문제 해결

### 브릿지 연결 실패

```bash
# Mosquitto 로그 확인
sudo journalctl -u mosquitto -f

# 원인:
# 1. EC2 보안그룹에서 8883 포트 미개방
# 2. 인증서 경로/권한 오류
# 3. Username/Password 불일치
```

### TLS 핸드셰이크 실패

```bash
# 인증서 검증
openssl x509 -in ca.crt -text -noout

# 서버 연결 테스트
openssl s_client -connect EC2_IP:8883 -CAfile ca.crt
```

---

## 참고 자료

- [Mosquitto Documentation](https://mosquitto.org/documentation/)
- [Paho MQTT Python](https://pypi.org/project/paho-mqtt/)
- [MQTT Bridge Configuration](https://mosquitto.org/man/mosquitto-conf-5.html)
- [TLS/SSL Certificate Generation](https://mosquitto.org/man/mosquitto-tls-7.html)
