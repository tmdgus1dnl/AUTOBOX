# 백엔드 연결 가이드

## 개요

프론트엔드는 `axios` 기반 API 클라이언트를 통해 백엔드와 통신합니다.  
목업 모드와 실제 백엔드 연결 모드를 환경 변수로 전환할 수 있습니다.

### 배포 아키텍처

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              EC2 Instance                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    HTTP     ┌─────────────┐    MQTT    ┌─────────────┐  │
│  │  Frontend   │────────────▶│   Backend   │◀──────────▶│  Mosquitto  │  │
│  │ (nginx:80)  │             │(FastAPI:8000)│           │ (MQTT:8883) │  │
│  └─────────────┘             └──────┬──────┘            └──────┬──────┘  │
│                                     │                          │         │
│                                     ▼                          │         │
│                              ┌─────────────┐                   │         │
│                              │    MySQL    │                   │         │
│                              │   (:3306)   │                   │         │
│                              └─────────────┘                   │         │
│                                                                │         │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ autobox-network ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │         │
└──────────────────────────────────────────────────────────────────────────┘
                                                                 │
                                                          non-TLS (8883)
                                                                 │
                                                                 ▼
                                                     ┌────────────────────┐
                                                     │   Raspberry Pi     │
                                                     │ (카메라/센서/모터) │
                                                     └────────────────────┘
```

---

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래 변수를 설정하세요.

### 필수 환경 변수

| 변수명 | 설명 | 기본값 | 예시 |
|--------|------|--------|------|
| `VITE_API_URL` | 백엔드 API 기본 주소 | `http://127.0.0.1:8000/api/v1` | `https://api.example.com/api/v1` |
| `VITE_MOCK_MODE` | 목업 모드 활성화 (`true`/`false`) | `false` | `true` |

### .env 파일 예시

```bash
# .env.development (개발 환경)
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_MOCK_MODE=false

# .env.production (배포 환경)
VITE_API_URL=https://api.yourserver.com/api/v1
VITE_MOCK_MODE=false
```

---

## 실행 모드

### 1. 실제 백엔드 연결 모드
```bash
npm run dev
```
- `VITE_API_URL`에 설정된 주소로 실제 API 호출
- 백엔드 서버가 실행 중이어야 함

### 2. 목업 모드 (백엔드 없이 테스트)
```bash
npm run dev:mock
```
- 백엔드 연결 없이 샘플 데이터로 UI 테스트
- `VITE_MOCK_MODE=true`가 자동 주입됨

---

## API 엔드포인트 목록

### 기본 URL
```
{VITE_API_URL} (기본: http://127.0.0.1:8000/api/v1)
```

### 대시보드 & 통계

| 메소드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/stats/regions` | 구역별 처리 현황 | `?date=YYYY-MM-DD` |
| GET | `/stats/daily` | 일별 처리 통계 | `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` |
| GET | `/stats/export` | 엑셀 다운로드 | `?date=YYYY-MM-DD` (선택) |

### 운송장 관리

| 메소드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/waybills` | 운송장 목록 조회 | Query params (page, size, status 등) |
| GET | `/waybills/{waybill_id}` | 운송장 상세 조회 (scan_logs 포함) | - |
| POST | `/waybills/scan` | 운송장 스캔 시작 | `{ camera_id: string }` |
| PUT | `/waybills/{waybill_id}/recognition` | OCR 인식 결과 저장 | OCR 데이터 객체 |
| PUT | `/waybills/{waybill_id}/start-sorting` | 분류 시작 | - |
| PUT | `/waybills/{waybill_id}/complete` | 분류 완료 | - |

### 알림 관리

| 메소드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/alerts` | 알림 목록 조회 | Query params (severity, resolved 등) |
| PATCH | `/alerts/{alert_id}/resolve` | 알림 해결 처리 | - |

### 시스템 & 장비

| 메소드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/system/status` | 시스템 상태 조회 | - |
| GET | `/regions` | 분류 구역 목록 | - |
| GET | `/cameras` | 카메라 목록 | - |
| GET | `/recognition/latest` | 최신 인식 정보 | - |
| GET | `/sensors/status` | 센서 상태 조회 | - |

### 차량 & 맵

| 메소드 | 엔드포인트 | 설명 | 파라미터 |
|--------|------------|------|----------|
| GET | `/vehicle/position` | 차량 위치 정보 | - |
| GET | `/map/data` | 맵 데이터 (경로, waypoints, 장애물) | - |

---

## API 응답 형식

### 성공 응답 예시
```json
{
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "size": 10
  }
}
```

### 구역별 통계 응답 (`/stats/regions`)
```json
{
  "data": [
    { "region_name": "서울", "completed": 67, "ready": 0, "moving": 0, "error": 0 },
    { "region_name": "부산", "completed": 59, "ready": 0, "moving": 0, "error": 0 }
  ]
}
```

### 시스템 상태 응답 (`/system/status`)
```json
{
  "data": {
    "battery_level": 85,
    "is_connected": true,
    "camera_status": "ACTIVE",
    "ocr_status": "RUNNING",
    "conveyor_status": "RUNNING",
    "last_updated": "2025-01-26T10:30:00Z"
  }
}
```

### 운송장 목록 응답 (`/waybills`)
```json
{
  "data": {
    "items": [
      {
        "waybill_id": "WB-001",
        "tracking_number": "123456789012",
        "destination": "서울",
        "status": "COMPLETED",
        "created_at": "2025-01-26T09:15:32",
        "completed_at": "2025-01-26T09:16:45",
        "process_time_sec": 73,
        "confidence_score": 98.5
      }
    ],
    "total": 270,
    "page": 1,
    "size": 100
  }
}
```

### 운송장 상세 응답 (`/waybills/{id}`)
```json
{
  "data": {
    "waybill_id": "WB-001",
    "tracking_number": "123456789012",
    "destination": "서울",
    "status": "COMPLETED",
    "created_at": "2025-01-26T09:15:32",
    "completed_at": "2025-01-26T09:16:45",
    "process_time_sec": 73,
    "confidence_score": 98.5,
    "scan_logs": [
      { "step": "SCAN", "timestamp": "...", "message": "운송장 스캔 시작" },
      { "step": "OCR", "timestamp": "...", "message": "OCR 인식 완료" },
      { "step": "CLASSIFY", "timestamp": "...", "message": "분류 구역 결정: 서울" },
      { "step": "MOVE", "timestamp": "...", "message": "컨베이어 이동 시작" },
      { "step": "COMPLETE", "timestamp": "...", "message": "분류 완료" }
    ]
  }
}
```

### 알림 목록 응답 (`/alerts`)
```json
{
  "data": {
    "items": [
      {
        "alert_id": "ALT-001",
        "alert_type": "OCR_ERROR",
        "message": "운송장 인식 실패: 567890123456",
        "waybill_id": "WB-005",
        "tracking_number": "567890123456",
        "created_at": "2025-01-26T09:25:50",
        "resolved": false,
        "severity": "HIGH"
      }
    ],
    "total": 3
  }
}
```

---

## 상태 코드 정의

### 운송장 상태 (`status`)
| 상태 | 설명 |
|------|------|
| `SCANNING` | 스캔 중 |
| `READY` | 분류 대기 |
| `MOVING` | 이동 중 |
| `COMPLETED` | 완료 |
| `ERROR` | 오류 |

### 알림 유형 (`alert_type`)
| 유형 | 설명 |
|------|------|
| `OCR_ERROR` | OCR 인식 실패 |
| `LOW_CONFIDENCE` | 낮은 신뢰도 인식 |
| `SYSTEM_WARNING` | 시스템 경고 |

### 알림 심각도 (`severity`)
| 심각도 | 설명 |
|--------|------|
| `HIGH` | 높음 (즉시 조치 필요) |
| `MEDIUM` | 중간 |
| `LOW` | 낮음 |

---

## 프론트엔드 API 함수 사용법

```javascript
// src/api/index.js에서 import
import {
  fetchDashboardStats,
  fetchDailyStats,
  fetchSystemStatus,
  fetchWaybills,
  fetchWaybillDetail,
  fetchAlerts,
  resolveAlert,
  fetchRegions,
  fetchCameras,
  fetchLatestRecognition,
  startWaybillScan,
  saveRecognitionResult,
  startSorting,
  completeSorting,
  getExportUrl,
  fetchVehiclePosition,
  fetchMapData,
  fetchSensorStatus,
  getMockMode
} from '@/api'

// 사용 예시
const response = await fetchDashboardStats('2025-01-26')
const data = response.data.data
```

---

## Docker 배포 (EC2 환경)

전체 스택은 `backend/docker-compose.yml`을 통해 한 번에 배포됩니다.

### 프로젝트 구조

```
S14P11A403/
├── backend/
│   ├── docker-compose.yml    # 전체 스택 정의 (여기서 실행)
│   ├── Dockerfile            # FastAPI 백엔드
│   ├── mqtt/                 # MQTT 설정/인증서
│   └── ...
└── frontend/
    ├── Dockerfile            # Vue.js 프론트엔드 (nginx)
    ├── nginx.conf
    └── ...
```

### 서비스 구성

| 서비스 | 컨테이너명 | 포트 | 설명 |
|--------|-----------|------|------|
| `mosquitto` | autobox-mqtt | 1883, 8883 | MQTT Broker (라즈베리파이 통신) |
| `mysql` | autobox-mysql | 3306 | MySQL DB (선택적, `--profile with-db`) |
| `backend` | autobox-backend | 8000 | FastAPI 백엔드 |
| `frontend` | autobox-frontend | 80 | Vue.js 프론트엔드 (nginx) |

### 환경 변수 설정

`backend/.env` 파일 생성:

```bash
# Database
DATABASE_URL=mysql+pymysql://root:root@mysql:3306/autobox
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=autobox

# Backend
DEBUG=false
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:5173,http://frontend

# MQTT
MQTT_TOPIC_PREFIX=autobox
MQTT_CLIENT_ID=autobox-backend
MQTT_USERNAME=backend
MQTT_PASSWORD=your_mqtt_password
MQTT_ENABLED=true

# Frontend
FRONTEND_PORT=80
VITE_API_URL=http://localhost:8000/api/v1
```

### 배포 명령어

```bash
# 1. backend 폴더로 이동
cd backend

# 2. 전체 스택 실행 (DB 포함)
docker-compose --profile with-db up -d --build

# 2-1. 외부 DB 사용 시 (MySQL 컨테이너 제외)
docker-compose up -d --build

# 3. 로그 확인
docker-compose logs -f frontend
docker-compose logs -f backend

# 4. 상태 확인
docker-compose ps

# 5. 중지
docker-compose down

# 6. 볼륨 포함 완전 삭제
docker-compose down -v
```

### EC2 배포 시 VITE_API_URL 설정

프론트엔드는 빌드 시점에 API URL이 번들에 포함됩니다.

```bash
# EC2 퍼블릭 IP 또는 도메인으로 설정
export VITE_API_URL=http://<EC2_PUBLIC_IP>:8000/api/v1

# 또는 .env 파일에 설정
echo "VITE_API_URL=http://your-domain.com:8000/api/v1" >> .env

# 빌드 실행
docker-compose up -d --build
```

> **중요**: `VITE_API_URL` 변경 시 프론트엔드를 다시 빌드해야 합니다.

### EC2 배포 체크리스트

- [ ] EC2 보안 그룹 포트 오픈: 80, 8000, 1883, 8883
- [ ] Docker 및 Docker Compose 설치
- [ ] 프로젝트 클론
- [ ] `backend/.env` 파일 설정
- [ ] MQTT 인증서 설정 (`backend/mqtt/certs/`)
- [ ] `VITE_API_URL`을 EC2 IP/도메인으로 설정
- [ ] `docker-compose up -d --build` 실행

### 빠른 배포 (EC2)

```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd S14P11A403/backend

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (VITE_API_URL 등)

# 3. 전체 스택 실행
docker-compose --profile with-db up -d --build

# 4. 상태 확인
docker-compose ps
```

---

## 백엔드 개발자를 위한 체크리스트

백엔드 구현 시 아래 사항을 확인하세요:

### API 응답 규격
- [ ] 모든 응답은 `{ data: ... }` 형식으로 래핑
- [ ] 목록 조회는 페이지네이션 지원 (`items`, `total`, `page`, `size`)
- [ ] 날짜 형식: ISO 8601 (`YYYY-MM-DDTHH:mm:ss`)
- [ ] 에러 응답 형식 통일

### Docker/배포
- [ ] CORS 설정: `http://localhost`, `http://frontend`, EC2 IP 허용
- [ ] Docker 네트워크(`autobox-network`)에서 `backend` 호스트명 접근 가능
- [ ] `/health` 엔드포인트 구현 (헬스체크용)
- [ ] MQTT 연결 설정 (`mosquitto:1883`)

### 환경 변수
- [ ] `DATABASE_URL` - MySQL 연결 문자열
- [ ] `CORS_ORIGINS` - 허용할 Origin 목록
- [ ] `MQTT_*` - MQTT 브로커 설정


```
docker build -t backend-frontend . && docker stop autobox-frontend && docker rm autobox-frontend && docker run -d --name autobox-frontend --network autobox-network -p 8081:80 backend-frontend
```