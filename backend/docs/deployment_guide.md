# AutoBox 배포 가이드 (Step-by-Step)

이 가이드는 DuckDNS 도메인 발급부터 HTTPS 적용, 그리고 Docker 배포까지의 전체 과정을 사용자 친화적으로 설명합니다. 복잡한 파일 경로는 배제하고, 실제 서버에서 입력해야 하는 **명령어**와 **설정 방법** 위주로 작성했습니다.

---

## 🚀 1단계: DuckDNS 도메인 만들기

무료로 나만의 도메인 주소(`xyz.duckdns.org`)를 만드는 과정입니다.

1. **[DuckDNS 홈페이지](https://www.duckdns.org/) 접속**
   - Google 또는 GitHub 계정으로 로그인합니다.

2. **도메인 추가**
   - 상단 입력창(sub domain)에 원하는 이름을 입력하고 `add domain` 버튼을 클릭합니다.
   - 예: `autoboxx`를 입력하면 -> `autoboxx.duckdns.org`가 생성됩니다.

3. **IP 주소 연결**
   - 생성된 도메인 옆의 `current ip` 입력란에 **내 AWS EC2 서버의 공인 IP (Elastic IP)**를 입력하고 `update ip` 버튼을 누릅니다.
   - _팁: EC2 인스턴스 요약 화면에서 '퍼블릭 IPv4 주소'를 확인하세요._

---

## 🛠️ 2단계: 서버 필수 프로그램 설치

EC2(Ubuntu) 서버에 접속해서 배포에 필요한 프로그램들을 설치합니다. 터미널에 아래 명령어들을 한 줄씩 순서대로 입력하세요.

### 1. 시스템 업데이트

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Docker & Docker Compose 설치

```bash
# Docker 설치
sudo apt install -y docker.io docker-compose

# 사용자 권한 설정 (sudo 없이 docker 쓰기 위함)
sudo usermod -aG docker $USER
# (여기서 로그아웃 후 다시 로그인해야 권한이 적용됩니다)
```

### 3. Nginx (웹 서버) & Certbot (SSL 인증서) 설치

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

---

## 🚢 3단계: Docker 컨테이너 실행

프로젝트 코드가 있는 폴더로 이동하여 서버를 실행합니다.

1. **소스 코드 폴더로 이동**

   ```bash
   # 예: 프로젝트 폴더가 git/S14P11A403 안에 있다고 가정할 때
   cd ~/git/S14P11A403/backend
   ```

   _(git clone을 아직 안 했다면 먼저 `git clone [주소]` 명령어로 코드를 받아오세요)_

2. **Docker 실행**
   ```bash
   # 백엔드, DB, MQTT 등 필요한 컨테이너들을 한 번에 실행합니다.
   docker-compose up -d --build
   ```

   - 이 명령어가 끝나면 백엔드(`8080`)와 프론트엔드(`8081`)가 내부적으로 실행됩니다.

---

## 🔒 4단계: HTTPS 적용 및 외부 연결 (Nginx 설정)

이제 외부에서 `https://내도메인`으로 접속했을 때, 내부의 Docker 컨테이너로 연결되도록 설정합니다.

### 1. Nginx 설정 파일 열기

터미널에서 아래 명령어로 설정 파일을 엽니다.

```bash
sudo nano /etc/nginx/sites-available/default
```

### 2. 설정 내용 작성 (복사 & 붙여넣기)

기존 내용을 모두 지우고 아래 내용을 붙여넣으세요. (`server_name` 부분은 본인의 DuckDNS 도메인으로 수정하세요!)

```nginx
server {
    # 1. 내 도메인 입력
    server_name autoboxx.duckdns.org;

    location / {
        # 2. 프론트엔드 Docker 컨테이너로 연결 (8081 포트)
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 기본 설정 (필요시 websocket 등 추가)
    listen 80;
}
```

작성 후 `Ctrl + O` (저장) -> `Enter` -> `Ctrl + X` (나가기)를 누릅니다.

### 3. Nginx 재시작

```bash
sudo systemctl restart nginx
```

### 4. SSL 인증서 발급 (HTTPS 자동 적용)

마지막으로 마법의 명령어 한 줄이면 HTTPS가 적용됩니다.

```bash
sudo certbot --nginx -d autoboxx.duckdns.org
```

- 이메일 주소를 입력하라고 나오면 입력합니다.
- 약관 동의(`Y`)를 합니다.
- **Redirect 설정**을 물어보면 `2`번 (Redirect all traffic to HTTPS)을 선택하는 것이 좋습니다.

---

## ✅ 5단계: 배포 완료 확인

이제 인터넷 브라우저를 켜고 주소창에 입력해 보세요.

👉 **https://autoboxx.duckdns.org**

자물쇠 아이콘(🔒)과 함께 사이트가 정상적으로 뜬다면 배포 성공입니다!

### 💡 요약: 나중에 업데이트할 때는?

코드를 수정한 뒤에는 **3단계**만 다시 하면 됩니다.

```bash
cd ~/git/S14P11A403/backend
docker-compose up -d --build
```

Nginx나 DuckDNS 설정은 한 번만 해두면 계속 유지됩니다.
