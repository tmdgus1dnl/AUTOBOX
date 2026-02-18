좋아. **(1) DB 스키마(DDL) + (2) FastAPI/Pydantic 스키마 + (3) 엔드포인트별 쿼리 설계**를 한 번에 정리해줄게.
(전제: `tracking_number`가 PK, `ScanLog`는 다대일, `DeviceStatus`는 독립. DB는 MySQL 8+ 또는 PostgreSQL 기준. 둘 다 가능한 SQL을 같이 제시)

---

## 1) DB 스키마(DDL) 설계

### 1.1 LogisticsItem

```sql
-- MySQL 8+
CREATE TABLE logistics_item (
  tracking_number   VARCHAR(50) PRIMARY KEY,
  destination       VARCHAR(20) NULL,
  status            ENUM('READY','MOVING','COMPLETED','ERROR') NOT NULL DEFAULT 'READY',
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at      DATETIME NULL,
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_logistics_item_created_at ON logistics_item (created_at);
CREATE INDEX idx_logistics_item_status_created ON logistics_item (status, created_at);
CREATE INDEX idx_logistics_item_destination_created ON logistics_item (destination, created_at);
```

```sql
-- PostgreSQL
CREATE TYPE logistics_status AS ENUM ('READY','MOVING','COMPLETED','ERROR');

CREATE TABLE logistics_item (
  tracking_number   VARCHAR(50) PRIMARY KEY,
  destination       VARCHAR(20),
  status            logistics_status NOT NULL DEFAULT 'READY',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at      TIMESTAMPTZ,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_logistics_item_created_at ON logistics_item (created_at);
CREATE INDEX idx_logistics_item_status_created ON logistics_item (status, created_at);
CREATE INDEX idx_logistics_item_destination_created ON logistics_item (destination, created_at);

-- updated_at 자동 갱신은 trigger 추천(필요하면 만들어줄게)
```

### 1.2 ScanLog

```sql
-- MySQL 8+
CREATE TABLE scan_log (
  id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
  tracking_number     VARCHAR(50) NOT NULL,
  camera_id           VARCHAR(20) NOT NULL,
  detected_destination VARCHAR(20) NULL,
  confidence_score    FLOAT NULL,
  scanned_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_scan_log_tracking
    FOREIGN KEY (tracking_number) REFERENCES logistics_item(tracking_number)
    ON DELETE CASCADE
);

CREATE INDEX idx_scan_log_tracking_scanned ON scan_log (tracking_number, scanned_at DESC);
CREATE INDEX idx_scan_log_scanned_at ON scan_log (scanned_at);
```

```sql
-- PostgreSQL
CREATE TABLE scan_log (
  id                  BIGSERIAL PRIMARY KEY,
  tracking_number     VARCHAR(50) NOT NULL REFERENCES logistics_item(tracking_number) ON DELETE CASCADE,
  camera_id           VARCHAR(20) NOT NULL,
  detected_destination VARCHAR(20),
  confidence_score    DOUBLE PRECISION,
  scanned_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_scan_log_tracking_scanned ON scan_log (tracking_number, scanned_at DESC);
CREATE INDEX idx_scan_log_scanned_at ON scan_log (scanned_at);
```

### 1.3 DeviceStatus

```sql
-- MySQL 8+
CREATE TABLE device_status (
  device_id         VARCHAR(50) PRIMARY KEY,
  battery_level     INT NOT NULL,
  is_connected      BOOLEAN NOT NULL,
  last_heartbeat    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  cpu_temperature   FLOAT NULL,
  location          VARCHAR(50) NULL,
  operation_status  ENUM('LOAD','TRANSPORT','STOP') NOT NULL DEFAULT 'STOP'
);

CREATE INDEX idx_device_status_heartbeat ON device_status (last_heartbeat);
```

```sql
-- PostgreSQL
CREATE TYPE operation_status AS ENUM ('LOAD','TRANSPORT','STOP');

CREATE TABLE device_status (
  device_id         VARCHAR(50) PRIMARY KEY,
  battery_level     INT NOT NULL,
  is_connected      BOOLEAN NOT NULL,
  last_heartbeat    TIMESTAMPTZ NOT NULL DEFAULT now(),
  cpu_temperature   DOUBLE PRECISION,
  location          VARCHAR(50),
  operation_status  operation_status NOT NULL DEFAULT 'STOP'
);

CREATE INDEX idx_device_status_heartbeat ON device_status (last_heartbeat);
```

---

## 2) Pydantic 스키마 설계 (FastAPI)

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, conint, confloat
from typing import Optional, List

class LogisticsStatus(str, Enum):
    READY = "READY"
    MOVING = "MOVING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class OperationStatus(str, Enum):
    LOAD = "LOAD"
    TRANSPORT = "TRANSPORT"
    STOP = "STOP"

class LogisticsItemOut(BaseModel):
    tracking_number: str
    destination: Optional[str] = None
    status: LogisticsStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    updated_at: datetime

class ScanLogOut(BaseModel):
    id: int
    tracking_number: str
    camera_id: str
    detected_destination: Optional[str] = None
    confidence_score: Optional[float] = None
    scanned_at: datetime

class LatestScanOut(BaseModel):
    camera_id: str
    detected_destination: Optional[str] = None
    confidence_score: Optional[float] = None
    scanned_at: datetime

class WaybillListItemOut(LogisticsItemOut):
    latest_scan: Optional[LatestScanOut] = None

class PageOut(BaseModel):
    items: List[WaybillListItemOut]
    total: int
    page: int
    size: int
    total_pages: int

class WaybillDetailOut(BaseModel):
    item: LogisticsItemOut
    scan_logs: List[ScanLogOut]

class ScanStartIn(BaseModel):
    camera_id: str

class RecognitionIn(BaseModel):
    destination_region: str
    ocr_confidence: confloat(ge=0, le=100)
    camera_id: str
    recognized_text: Optional[str] = None
    delivery_type_id: Optional[str] = None
    category_id: Optional[str] = None

class StartSortingOut(BaseModel):
    tracking_number: str
    status: LogisticsStatus
    updated_at: datetime

class CompleteOut(BaseModel):
    tracking_number: str
    status: LogisticsStatus
    completed_at: datetime
    updated_at: datetime
    process_time_sec: int

class ErrorIn(BaseModel):
    error_reason: str

class ErrorOut(BaseModel):
    tracking_number: str
    status: LogisticsStatus
    updated_at: datetime
    alert_id: int

class DeviceStatusIn(BaseModel):
    device_id: str
    battery_level: conint(ge=0, le=100)
    is_connected: bool
    cpu_temperature: Optional[float] = None
    location: Optional[str] = None
    operation_status: OperationStatus
```

---

## 3) 핵심 쿼리 설계 (엔드포인트별)

### 3.1 `GET /waybills` — 페이지 + 필터 + latest_scan 포함

#### ✅ 방법 A (권장, Postgres / MySQL 8 모두 가능): 윈도우 함수로 latest scan 1개만 조인

```sql
-- 공통(개념): scan_log에서 tracking_number별 최신 1개를 rn=1로 추려 조인
WITH latest AS (
  SELECT
    sl.*,
    ROW_NUMBER() OVER (PARTITION BY sl.tracking_number ORDER BY sl.scanned_at DESC, sl.id DESC) AS rn
  FROM scan_log sl
)
SELECT
  li.tracking_number,
  li.destination,
  li.status,
  li.created_at,
  li.completed_at,
  li.updated_at,

  l.camera_id AS latest_camera_id,
  l.detected_destination AS latest_detected_destination,
  l.confidence_score AS latest_confidence_score,
  l.scanned_at AS latest_scanned_at
FROM logistics_item li
LEFT JOIN latest l
  ON l.tracking_number = li.tracking_number
 AND l.rn = 1
WHERE 1=1
  -- 날짜 필터(선택)
  AND (:date IS NULL OR li.created_at >= :date_start AND li.created_at < :date_end)
  -- 상태 필터(선택)
  AND (:status IS NULL OR li.status = :status)
  -- 구역 필터(선택)
  AND (:destination IS NULL OR li.destination = :destination)
ORDER BY li.created_at DESC, li.tracking_number DESC
LIMIT :size OFFSET :offset;
```

**COUNT 쿼리(페이징 total용)**

```sql
SELECT COUNT(*)
FROM logistics_item li
WHERE 1=1
  AND (:date IS NULL OR li.created_at >= :date_start AND li.created_at < :date_end)
  AND (:status IS NULL OR li.status = :status)
  AND (:destination IS NULL OR li.destination = :destination);
```

> 인덱스가 `logistics_item(status, created_at)` / `logistics_item(destination, created_at)`이면 필터+정렬이 빠르고,
> `scan_log(tracking_number, scanned_at desc)`가 latest 추출에 핵심입니다.

---

### 3.2 `GET /waybills/{waybill_id}` → 실전에서는 `{tracking_number}`가 더 낫다

너는 아직 `{waybill_id}`를 라우팅에 쓰고 있는데, DB 모델이 `tracking_number` PK라서 2가지 선택지야:

#### 선택 1) API는 `{waybill_id}` 유지, DB에 매핑 테이블 둠 (권장)

```sql
CREATE TABLE waybill_map (
  waybill_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  tracking_number VARCHAR(50) NOT NULL UNIQUE
);
```

* `scan_start` 시 `waybill_map` 생성하고 `tracking_number`를 연결
* 이후 모든 `{waybill_id}` API는 `tracking_number`로 변환해서 처리

**조회 흐름**

```sql
SELECT tracking_number FROM waybill_map WHERE waybill_id = :waybill_id;
```

그 다음 상세:

```sql
SELECT * FROM logistics_item WHERE tracking_number = :tracking_number;

SELECT *
FROM scan_log
WHERE tracking_number = :tracking_number
ORDER BY scanned_at DESC, id DESC
LIMIT 200;
```

#### 선택 2) 그냥 `{tracking_number}`로 바꾼다 (가장 단순/깔끔)

* `/waybills/{tracking_number}`

---

### 3.3 `POST /waybills/scan` — tracking_number 발급 + 생성(트랜잭션)

```sql
-- 1) tracking_number 생성은 앱에서 생성(TRK-YYYY-###) 추천
INSERT INTO logistics_item (tracking_number, status, created_at, updated_at)
VALUES (:tracking_number, 'READY', NOW(), NOW());

-- (선택) waybill_id 매핑 유지 시
INSERT INTO waybill_map (tracking_number) VALUES (:tracking_number);
```

> **트랜잭션**으로 묶어야 “아이템은 있는데 map이 없다” 같은 꼬임이 안 생김.

---

### 3.4 `PUT /waybills/{id}/recognition` — ScanLog 추가 + LogisticsItem 갱신

```sql
-- tracking_number 확보(waybill_id라면 map 조회)
-- 1) scan_log insert
INSERT INTO scan_log (
  tracking_number, camera_id, detected_destination, confidence_score, scanned_at
) VALUES (
  :tracking_number, :camera_id, :destination, :confidence, NOW()
);

-- 2) logistics_item update (destination/status/updated_at)
UPDATE logistics_item
SET destination = :destination,
    status = 'READY',
    updated_at = NOW()
WHERE tracking_number = :tracking_number;
```

> 여기서 `status`를 `READY`로 두는 이유: “인식 완료”는 내부 이벤트고, 프론트 표준 상태는 READY로 묶었기 때문.

---

### 3.5 `PUT /waybills/{id}/start-sorting` — MOVING

```sql
UPDATE logistics_item
SET status = 'MOVING',
    updated_at = NOW()
WHERE tracking_number = :tracking_number;
```

---

### 3.6 `PUT /waybills/{id}/complete` — COMPLETED + process_time_sec 계산

```sql
UPDATE logistics_item
SET status = 'COMPLETED',
    completed_at = NOW(),
    updated_at = NOW()
WHERE tracking_number = :tracking_number;

-- process_time_sec는 created_at과 completed_at 차이로 계산
-- MySQL:
SELECT TIMESTAMPDIFF(SECOND, created_at, completed_at) AS process_time_sec
FROM logistics_item
WHERE tracking_number = :tracking_number;

-- PostgreSQL:
SELECT EXTRACT(EPOCH FROM (completed_at - created_at))::int AS process_time_sec
FROM logistics_item
WHERE tracking_number = :tracking_number;
```

---

### 3.7 `PUT /waybills/{id}/error` — ERROR + alert 생성 연동(트랜잭션)

```sql
UPDATE logistics_item
SET status = 'ERROR',
    updated_at = NOW()
WHERE tracking_number = :tracking_number;

-- alerts 테이블이 있다면 INSERT 후 alert_id 반환(생략 가능)
```

---

### 3.8 `PUT /system/status` — DeviceStatus UPSERT

```sql
-- MySQL
INSERT INTO device_status (
  device_id, battery_level, is_connected, last_heartbeat,
  cpu_temperature, location, operation_status
) VALUES (
  :device_id, :battery_level, :is_connected, NOW(),
  :cpu_temperature, :location, :operation_status
)
ON DUPLICATE KEY UPDATE
  battery_level = VALUES(battery_level),
  is_connected = VALUES(is_connected),
  last_heartbeat = NOW(),
  cpu_temperature = VALUES(cpu_temperature),
  location = VALUES(location),
  operation_status = VALUES(operation_status);
```

```sql
-- PostgreSQL
INSERT INTO device_status (
  device_id, battery_level, is_connected, last_heartbeat,
  cpu_temperature, location, operation_status
) VALUES (
  :device_id, :battery_level, :is_connected, now(),
  :cpu_temperature, :location, :operation_status
)
ON CONFLICT (device_id) DO UPDATE SET
  battery_level = EXCLUDED.battery_level,
  is_connected = EXCLUDED.is_connected,
  last_heartbeat = now(),
  cpu_temperature = EXCLUDED.cpu_temperature,
  location = EXCLUDED.location,
  operation_status = EXCLUDED.operation_status;
```

---

## 4) “latest_scan”을 더 빠르게 하는 옵션 (규모 커질 때)

ScanLog가 엄청 커지면, 리스트에서 매번 window function이 부담될 수 있어.

### 옵션 1) LogisticsItem에 latest_scan_id 컬럼 유지(비정규화)

* `logistics_item.latest_scan_id BIGINT NULL`
* ScanLog insert 직후 해당 id로 update
* 리스트는 그냥 join 한번이면 끝

```sql
ALTER TABLE logistics_item ADD COLUMN latest_scan_id BIGINT NULL;
CREATE INDEX idx_logistics_item_latest_scan_id ON logistics_item (latest_scan_id);

-- ScanLog insert 후 last_insert_id() 를 받아서
UPDATE logistics_item
SET latest_scan_id = :scan_log_id,
    destination = :destination,
    updated_at = NOW()
WHERE tracking_number = :tracking_number;

-- 리스트 조인
SELECT li.*, sl.camera_id, sl.detected_destination, sl.confidence_score, sl.scanned_at
FROM logistics_item li
LEFT JOIN scan_log sl ON sl.id = li.latest_scan_id
...
```

---

## 5) 내가 추천하는 “현실적인 운영” 베스트 조합

* **DB는 ERD 그대로**(tracking_number PK) + (가능하면) `waybill_map`으로 `{waybill_id}` 라우팅 유지
* 리스트는 **윈도우 함수 방식(A)** 로 시작
* 트래픽/데이터 커지면 `latest_scan_id` 방식으로 최적화

---

## 6) 실시간 모니터링 테이블 (신규 추가)

### 6.1 VehiclePosition (차량 위치)

```sql
-- MySQL 8+
CREATE TABLE vehicle_position (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  vehicle_id      VARCHAR(50) NOT NULL COMMENT '차량 ID',
  x               FLOAT NOT NULL COMMENT 'X 좌표',
  y               FLOAT NOT NULL COMMENT 'Y 좌표',
  angle           FLOAT NOT NULL DEFAULT 0 COMMENT '차량 방향 (0-360도)',
  speed           FLOAT NOT NULL DEFAULT 0 COMMENT '속도 (km/h)',
  battery         INT NOT NULL DEFAULT 100 COMMENT '배터리 레벨 (0-100)',
  mode            VARCHAR(20) NOT NULL DEFAULT 'IDLE' COMMENT '운행 모드 (AUTO, MANUAL, IDLE)',
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_vp_vehicle_id ON vehicle_position (vehicle_id);
CREATE INDEX idx_vp_updated_at ON vehicle_position (updated_at);

ALTER TABLE vehicle_position
  ADD CONSTRAINT chk_vp_battery CHECK (battery BETWEEN 0 AND 100);
```

> **참고**: 차량별 최신 위치만 필요하므로 UPSERT 방식으로 업데이트합니다.

---

### 6.2 MapData (맵 데이터)

```sql
-- MySQL 8+
CREATE TABLE map_data (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  map_id          VARCHAR(50) NOT NULL UNIQUE COMMENT '맵 식별자',
  name            VARCHAR(100) NULL COMMENT '맵 이름',
  waypoints       JSON NULL COMMENT '웨이포인트 배열 (JSON)',
  buildings       JSON NULL COMMENT '건물/장애물 배열 (JSON)',
  obstacles       JSON NULL COMMENT '동적 장애물 배열 (JSON)',
  roads           JSON NULL COMMENT '도로 경로 배열 (JSON)',
  zones           JSON NULL COMMENT '작업 구역 배열 (JSON)',
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_md_map_id ON map_data (map_id);
```

**JSON 데이터 형식 예시**:

```json
// waypoints
[
  { "id": 1, "label": "A", "x": 200, "y": 300, "color": "#10b981", "type": "pickup" },
  { "id": 2, "label": "B", "x": 500, "y": 200, "color": "#f59e0b", "type": "dropoff" }
]

// buildings
[
  { "id": 1, "x": 150, "y": 150, "width": 100, "height": 80, "type": "building" }
]
```

---

### 6.3 SensorStatus (센서 상태)

```sql
-- MySQL 8+
CREATE TABLE sensor_status (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  vehicle_id      VARCHAR(50) NOT NULL COMMENT '차량 ID',
  sensor_name     VARCHAR(50) NOT NULL COMMENT '센서 이름 (LIDAR, Camera, GPS, IMU)',
  sensor_type     VARCHAR(50) NULL COMMENT '센서 유형',
  status          VARCHAR(20) NOT NULL DEFAULT 'ok' COMMENT '상태 (ok, warning, error, offline)',
  health          INT NULL DEFAULT 100 COMMENT '센서 상태 (0-100%)',
  value           VARCHAR(200) NULL COMMENT '센서 값 또는 설명',
  data            JSON NULL COMMENT '센서 상세 데이터 (JSON)',
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_ss_vehicle_id ON sensor_status (vehicle_id);
CREATE INDEX idx_ss_vehicle_sensor ON sensor_status (vehicle_id, sensor_name);
CREATE INDEX idx_ss_updated_at ON sensor_status (updated_at);

ALTER TABLE sensor_status
  ADD CONSTRAINT chk_ss_health CHECK (health IS NULL OR (health BETWEEN 0 AND 100));
```

---

### 6.4 초기 데이터 삽입

```sql
-- 기본 맵 데이터
INSERT INTO map_data (map_id, name, waypoints, buildings, obstacles) VALUES (
  'default',
  '물류 센터 기본 맵',
  '[
    {"id": 1, "label": "A", "x": 200, "y": 300, "color": "#10b981", "type": "pickup"},
    {"id": 2, "label": "B", "x": 500, "y": 200, "color": "#f59e0b", "type": "dropoff"},
    {"id": 3, "label": "C", "x": 750, "y": 300, "color": "#ef4444", "type": "dropoff"},
    {"id": 4, "label": "D", "x": 500, "y": 600, "color": "#3b82f6", "type": "charging"}
  ]',
  '[
    {"id": 1, "x": 150, "y": 150, "width": 100, "height": 80, "type": "building"},
    {"id": 2, "x": 650, "y": 150, "width": 120, "height": 100, "type": "building"},
    {"id": 3, "x": 150, "y": 450, "width": 90, "height": 110, "type": "building"},
    {"id": 4, "x": 700, "y": 450, "width": 100, "height": 90, "type": "building"}
  ]',
  '[]'
);

-- 기본 차량 위치
INSERT INTO vehicle_position (vehicle_id, x, y, angle, speed, battery, mode) VALUES
  ('AGV-001', 450.0, 350.0, 0, 0, 100, 'IDLE');

-- 기본 센서 상태
INSERT INTO sensor_status (vehicle_id, sensor_name, sensor_type, status, health, value) VALUES
  ('AGV-001', 'LIDAR', 'lidar', 'ok', 100, '정상 (360°)'),
  ('AGV-001', 'Camera', 'rgb_camera', 'ok', 100, '정상 (1080p)'),
  ('AGV-001', 'GPS', 'gnss', 'ok', 95, '정확도 ±2m'),
  ('AGV-001', 'IMU', 'inertial', 'ok', 100, '정상');
```

---

## 7) 전체 ERD 요약 (업데이트됨)

```
┌─────────────────────┐     ┌─────────────────────┐
│   logistics_item    │────▶│      scan_log       │
│   (tracking_number) │ 1:N │  (id, tracking_no)  │
└─────────────────────┘     └─────────────────────┘
          │
          ▼
┌─────────────────────┐
│     waybill_map     │
│ (waybill_id ↔ TRK)  │
└─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│   device_status     │     │   vehicle_position  │
│     (device_id)     │     │    (vehicle_id)     │
└─────────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│     map_data        │     │   sensor_status     │
│     (map_id)        │     │ (vehicle_id, name)  │
└─────────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│      region         │     │       alert         │
│    (region_id)      │     │     (alert_id)      │
└─────────────────────┘     └─────────────────────┘

┌─────────────────────┐
│      camera         │
│    (camera_id)      │
└─────────────────────┘
```

---