# AutoBox MQTT Broker Configuration

Edge-Cloud 하이브리드 아키텍처를 위한 MQTT 브로커 설정 가이드입니다.

## 초기 설정

### 1. TLS 인증서 생성

```bash
cd backend/mqtt/certs
chmod +x generate-certs.sh
./generate-certs.sh 43.201.254.235
```

### 2. 사용자 비밀번호 설정

```bash
cd backend/mqtt/config
chmod +x generate-passwd.sh
./generate-passwd.sh
```

### 3. Docker 컨테이너 시작

```bash
docker-compose up -d
docker-compose logs -f mosquitto
```

## 보안 기능

- TLS 1.2/1.3 암호화 (Port 8883)
- Username/Password 인증
- Topic ACL 접근 제어

자세한 내용은 프로젝트 루트의 docs/Communication_Architecture.md를 참조하세요.
