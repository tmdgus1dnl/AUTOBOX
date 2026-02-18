# HTTPS 설정 가이드 (Let's Encrypt + Nginx)

이 문서는 autoboxx.duckdns.org 도메인에 HTTPS를 설정하는 방법을 설명합니다.

## 최종 구조

```
[User Browser]
    ↓ HTTPS (443)
[Host Nginx] autoboxx.duckdns.org
    ├── /         → http://127.0.0.1:8081 (프론트엔드 컨테이너)
    └── /api/v1/  → http://127.0.0.1:8080/api/v1/ (백엔드 컨테이너)

[Docker Containers]
├── autobox-frontend (8081:80)
├── autobox-backend (8080:8000)
└── autobox-mqtt (1883, 8883)
```

---

## 1. Docker Compose 설정

### 프론트엔드 포트 변경

`docker-compose.yml`에서 프론트엔드 포트를 80에서 8081로 변경:

```yaml
frontend:
  ports:
    - "8081:80"  # 호스트 Nginx가 80/443을 사용하므로
```

---

## 2. 환경변수 설정

### backend/.env

```env
# CORS에 도메인 추가
CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:5173,https://autoboxx.duckdns.org,http://autoboxx.duckdns.org

# 프론트엔드 API URL (상대경로)
VITE_API_URL=/api/v1
```

### frontend/.env

```env
VITE_API_URL=/api/v1
```

---

## 3. Docker 재시작

```bash
cd backend
docker compose down
docker compose up -d --build
```

확인:
```bash
curl http://localhost:8081  # 프론트엔드
curl http://localhost:8080/health  # 백엔드
```

---

## 4. 호스트 Nginx + Certbot 설치

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
sudo systemctl enable nginx
```

---

## 5. Nginx 리버스 프록시 설정

### 설정 파일 생성

```bash
sudo nano /etc/nginx/sites-available/autoboxx
```

내용:

```nginx
server {
    listen 80;
    server_name autoboxx.duckdns.org;

    # 프론트엔드
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 백엔드 API
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8080/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 활성화 및 테스트

```bash
# 기존 default 설정 비활성화 (포트 충돌 방지)
sudo rm /etc/nginx/sites-enabled/default

# 새 설정 활성화
sudo ln -s /etc/nginx/sites-available/autoboxx /etc/nginx/sites-enabled/autoboxx

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

---

## 6. HTTPS 인증서 발급 (Let's Encrypt)

```bash
sudo certbot --nginx -d autoboxx.duckdns.org
```

옵션 선택:
- 약관 동의
- HTTP → HTTPS 리다이렉트: **2번 선택**

### 자동 발급 (비대화형)

```bash
sudo certbot --nginx -d autoboxx.duckdns.org \
  --non-interactive \
  --agree-tos \
  --email your-email@example.com \
  --redirect
```

---

## 7. 인증서 갱신

인증서는 90일마다 자동 갱신됩니다. 수동 테스트:

```bash
sudo certbot renew --dry-run
```

---

## 트러블슈팅

### 포트 충돌

```bash
# 포트 사용 확인
sudo lsof -i :80
sudo lsof -i :8081

# Nginx 중지 후 Docker 먼저 시작
sudo systemctl stop nginx
docker compose up -d
sudo systemctl start nginx
```

### API URL이 localhost로 빌드되는 경우

1. `.vite` 캐시 삭제:
```bash
rm -rf frontend/.vite
```

2. Docker 이미지 완전 재빌드:
```bash
docker compose down
docker rmi backend-frontend -f
docker builder prune -af
docker compose build --no-cache frontend
docker compose up -d
```

3. 빌드된 URL 확인:
```bash
docker exec autobox-frontend grep -o 'baseURL:"[^"]*"' /usr/share/nginx/html/assets/index*.js
```

### 보안그룹 확인

AWS EC2 보안그룹에서 다음 포트 허용:
- 80 (HTTP)
- 443 (HTTPS)
- 8080 (백엔드, 필요시)
- 8883 (MQTT TLS)

---

## 최종 확인

```bash
# HTTPS 프론트엔드
curl -I https://autoboxx.duckdns.org

# HTTPS 백엔드 API
curl https://autoboxx.duckdns.org/api/v1/system/status
```
