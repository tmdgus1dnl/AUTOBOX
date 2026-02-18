# MQTT 테스트 스크립트

EC2 서버와 라즈베리파이 간 MQTT 통신 테스트용 스크립트

## 토픽 구조

| 방향 | 토픽 |
|------|------|
| 서버 → 라즈베리파이 | `server_msg/#` |
| 라즈베리파이 → 서버 | `factory_msg/#` |

---

## EC2 서버에서 테스트

### 설치

```bash
pip install paho-mqtt
```

### 실행

```bash
cd backend/test

# 발행만 (서버 → 라파)
python mqtt_test.py send

# 구독만 (라파 → 서버)
python mqtt_test.py receive

# 양방향
python mqtt_test.py both
```

---

## 라즈베리파이에서 테스트

### 1. 파일 복사

```bash
# EC2에서 라즈베리파이로 복사
scp backend/test/raspi_test.py pi@<RASPI_IP>:/home/pi/

# 인증서도 복사 (아직 안 했다면)
scp backend/mqtt/certs/ca.crt pi@<RASPI_IP>:/home/pi/autobox/certs/
```

### 2. 설정 수정

`raspi_test.py` 파일을 열어서 수정:

```python
BROKER_HOST = "YOUR_EC2_IP"  # ← EC2 퍼블릭 IP로 변경!
PASSWORD = "qwert123"        # ← 실제 비밀번호로 변경!
CA_CERT = "/home/pi/autobox/certs/ca.crt"  # ← 경로 확인!
```

### 3. 실행

```bash
pip install paho-mqtt

# 발행 (라파 → 서버)
python raspi_test.py send

# 구독 (서버 → 라파)
python raspi_test.py receive

# 양방향
python raspi_test.py both
```

---

## 테스트 시나리오

### 1. EC2 → 라즈베리파이

| 순서 | 위치 | 명령 |
|------|------|------|
| 1 | 라즈베리파이 | `python raspi_test.py receive` |
| 2 | EC2 | `python mqtt_test.py send` → Enter |
| 3 | 라즈베리파이 | 메시지 수신 확인 |

### 2. 라즈베리파이 → EC2

| 순서 | 위치 | 명령 |
|------|------|------|
| 1 | EC2 | `python mqtt_test.py receive` |
| 2 | 라즈베리파이 | `python raspi_test.py send` → Enter |
| 3 | EC2 | 메시지 수신 확인 |

### 3. 양방향 동시

| 터미널 | 위치 | 명령 |
|--------|------|------|
| 1 | EC2 | `python mqtt_test.py both` |
| 2 | 라즈베리파이 | `python raspi_test.py both` |

---

## 문제 해결

### 연결 실패

```
[✗] 연결 실패: [Errno 111] Connection refused
```

- EC2 보안그룹에서 8883 포트 열려있는지 확인
- `docker ps`로 mosquitto 컨테이너 실행 중인지 확인

### 인증 실패

```
[✗] 연결 실패: 5 (Not authorized)
```

- 비밀번호 확인
- ACL 파일에서 토픽 권한 확인

### 인증서 오류

```
ssl.SSLCertVerificationError
```

- ca.crt 파일 경로 확인
- 파일 존재 여부 확인: `ls -la /home/pi/autobox/certs/`
