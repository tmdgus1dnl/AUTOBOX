/* =========================================================
   AutoBox Database (MySQL 8.x)
   ========================================================= */

-- ★ Azure MySQL 사용 시 (SSAFY 프로젝트)
USE S14P11A403;

-- 로컬 개발용(with-db 프로필)은 아래 주석 해제:
-- CREATE DATABASE IF NOT EXISTS autobox
--   DEFAULT CHARACTER SET utf8mb4
--   DEFAULT COLLATE utf8mb4_0900_ai_ci;
-- USE autobox;

/* =========================================================
   1) LogisticsItem (물류 아이템 메인)
   - tracking_number: 프론트 ERD의 PK
   - destination/status/created_at/completed_at/updated_at: 프론트 필드와 1:1
   ========================================================= */

DROP TABLE IF EXISTS scan_log;
DROP TABLE IF EXISTS waybill_map;
DROP TABLE IF EXISTS logistics_item;
DROP TABLE IF EXISTS device_status;
DROP TABLE IF EXISTS region;
DROP TABLE IF EXISTS camera;
DROP TABLE IF EXISTS alert;
DROP TABLE IF EXISTS vehicle_position;
DROP TABLE IF EXISTS map_data;
DROP TABLE IF EXISTS sensor_status;

CREATE TABLE logistics_item (
  tracking_number VARCHAR(50) NOT NULL COMMENT '운송장 번호 (고유값)',
  destination     VARCHAR(20) NULL COMMENT '목표 지역 (region_id)',
  status          ENUM('READY','MOVING','COMPLETED','ERROR') NOT NULL DEFAULT 'READY' COMMENT '상태',
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  completed_at    DATETIME NULL COMMENT '완료 시간',
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '최종 수정 시간',
  PRIMARY KEY (tracking_number),
  INDEX idx_li_created_at (created_at),
  INDEX idx_li_status_created (status, created_at),
  INDEX idx_li_destination_created (destination, created_at)
) ENGINE=InnoDB COMMENT='물류 아이템(메인)';


/* =========================================================
   2) ScanLog (스캔 이력)
   - 한 운송장(tracking_number)에 대해 여러 스캔이 쌓임 (1:N)
   - 최신 스캔 1개(latest_scan)를 빠르게 뽑기 위한 복합 인덱스 포함
   ========================================================= */

CREATE TABLE scan_log (
  id                   BIGINT NOT NULL AUTO_INCREMENT COMMENT '로그 고유 ID',
  tracking_number      VARCHAR(50) NOT NULL COMMENT '운송장 번호 (FK)',
  camera_id            VARCHAR(20) NOT NULL COMMENT '촬영한 카메라 ID',
  detected_destination VARCHAR(20) NULL COMMENT 'AI가 인식한 지역명(region_id)',
  confidence_score     FLOAT NULL COMMENT 'AI 신뢰도(0~100)',
  scanned_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '스캔 시간',
  PRIMARY KEY (id),
  CONSTRAINT fk_scan_log_tracking
    FOREIGN KEY (tracking_number) REFERENCES logistics_item(tracking_number)
    ON DELETE CASCADE,
  INDEX idx_sl_tracking_scanned (tracking_number, scanned_at DESC, id DESC),
  INDEX idx_sl_scanned_at (scanned_at)
) ENGINE=InnoDB COMMENT='스캔 로그(이력)';


/* =========================================================
   3) DeviceStatus (장치 상태)
   - 젯슨/라즈베리파이/로봇 등 단말의 최신 상태 1행으로 유지(UPSERT)
   ========================================================= */

CREATE TABLE device_status (
  device_id        VARCHAR(50) NOT NULL COMMENT '기기 ID (ROBOT_01 등)',
  battery_level    INT NOT NULL COMMENT '배터리 잔량(0~100)',
  is_connected     BOOLEAN NOT NULL COMMENT '연결 상태',
  last_heartbeat   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '마지막 통신 시간',
  cpu_temperature  FLOAT NULL COMMENT 'CPU 온도',
  location         VARCHAR(50) NULL COMMENT '위치 정보(좌표 또는 구역명)',
  operation_status ENUM('LOAD','TRANSPORT','STOP') NOT NULL DEFAULT 'STOP' COMMENT '동작 상태',
  PRIMARY KEY (device_id),
  INDEX idx_ds_heartbeat (last_heartbeat)
) ENGINE=InnoDB COMMENT='장치 상태(최신)';


/* =========================================================
   4) (선택) waybill_id 라우팅 유지용 매핑 테이블
   - 너의 API는 /waybills/{waybill_id} 형태가 존재
   - DB 메인은 tracking_number라서 ID<->tracking_number 매핑을 둬서 깔끔하게 연결
   ========================================================= */

CREATE TABLE waybill_map (
  waybill_id       BIGINT NOT NULL AUTO_INCREMENT COMMENT '내부 운송장 ID',
  tracking_number  VARCHAR(50) NOT NULL COMMENT '운송장 번호',
  PRIMARY KEY (waybill_id),
  UNIQUE KEY uk_waybill_map_tracking (tracking_number),
  CONSTRAINT fk_waybill_map_tracking
    FOREIGN KEY (tracking_number) REFERENCES logistics_item(tracking_number)
    ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='내부 ID(waybill_id) <-> tracking_number 매핑';


/* =========================================================
   5) (선택) Region / Camera / Alert
   - 너의 API 문서에 이미 존재하는 자원들
   - 프론트 메타데이터/운영 대시보드/알림 기능을 위해 DB로 저장하는 구조
   ========================================================= */

CREATE TABLE region (
  region_id      VARCHAR(20) NOT NULL COMMENT '구역 ID (seoul-a)',
  region_name    VARCHAR(50) NOT NULL COMMENT '구역 이름 (서울-A)',
  region_detail  VARCHAR(50) NULL COMMENT '상세(마포)',
  display_order  INT NOT NULL DEFAULT 0 COMMENT '표시 순서',
  is_active      BOOLEAN NOT NULL DEFAULT TRUE COMMENT '활성 여부',
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (region_id),
  INDEX idx_region_active_order (is_active, display_order)
) ENGINE=InnoDB COMMENT='구역 메타데이터';


CREATE TABLE camera (
  camera_id        VARCHAR(20) NOT NULL COMMENT '카메라 ID',
  camera_name      VARCHAR(100) NOT NULL COMMENT '카메라 이름',
  camera_type      ENUM('live','capture') NOT NULL COMMENT '카메라 타입',
  location         VARCHAR(100) NULL COMMENT '설치 위치',
  stream_url       VARCHAR(255) NULL COMMENT '스트림 URL',
  status           ENUM('online','offline') NOT NULL DEFAULT 'offline' COMMENT '상태',
  last_heartbeat   DATETIME NULL COMMENT '마지막 하트비트',
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (camera_id),
  INDEX idx_camera_status (status),
  INDEX idx_camera_heartbeat (last_heartbeat)
) ENGINE=InnoDB COMMENT='카메라 메타/상태';


CREATE TABLE alert (
  alert_id      BIGINT NOT NULL AUTO_INCREMENT COMMENT '알림 ID',
  alert_type    VARCHAR(50) NOT NULL COMMENT '알림 타입(ocr_error 등)',
  severity      ENUM('info','warning','critical') NOT NULL DEFAULT 'info' COMMENT '심각도',
  title         VARCHAR(100) NOT NULL COMMENT '제목',
  message       VARCHAR(500) NOT NULL COMMENT '메시지',
  source_type   VARCHAR(30) NULL COMMENT '출처 타입(waybill/system 등)',
  source_id     VARCHAR(50) NULL COMMENT '출처 ID(waybill_id/tracking_number 등)',
  is_resolved   BOOLEAN NOT NULL DEFAULT FALSE COMMENT '해결 여부',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at   DATETIME NULL,
  PRIMARY KEY (alert_id),
  INDEX idx_alert_resolved_created (is_resolved, created_at),
  INDEX idx_alert_severity_created (severity, created_at)
) ENGINE=InnoDB COMMENT='알림';


/* =========================================================
   6) (선택) 데이터 무결성 보강: CHECK (MySQL 8.0.16+에서 동작)
   ========================================================= */

ALTER TABLE device_status
  ADD CONSTRAINT chk_ds_battery CHECK (battery_level BETWEEN 0 AND 100);

ALTER TABLE scan_log
  ADD CONSTRAINT chk_sl_confidence CHECK (confidence_score IS NULL OR (confidence_score BETWEEN 0 AND 100));


/* =========================================================
   7) VehiclePosition (차량 위치)
   - 실시간 차량 위치 정보 저장
   - vehicle_id별 최신 1행만 필요할 수 있음 (UPSERT 방식)
   ========================================================= */

CREATE TABLE vehicle_position (
  id              BIGINT NOT NULL AUTO_INCREMENT COMMENT '위치 레코드 ID',
  vehicle_id      VARCHAR(50) NOT NULL COMMENT '차량 ID',
  x               FLOAT NOT NULL COMMENT 'X 좌표',
  y               FLOAT NOT NULL COMMENT 'Y 좌표',
  angle           FLOAT NOT NULL DEFAULT 0 COMMENT '차량 방향 (0-360도)',
  speed           FLOAT NOT NULL DEFAULT 0 COMMENT '속도 (km/h)',
  battery         INT NOT NULL DEFAULT 100 COMMENT '배터리 레벨 (0-100)',
  mode            VARCHAR(20) NOT NULL DEFAULT 'IDLE' COMMENT '운행 모드 (AUTO, MANUAL, IDLE)',
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '마지막 업데이트',
  PRIMARY KEY (id),
  INDEX idx_vp_vehicle_id (vehicle_id),
  INDEX idx_vp_updated_at (updated_at)
) ENGINE=InnoDB COMMENT='차량 위치 정보';


/* =========================================================
   8) MapData (맵 데이터)
   - 웨이포인트, 건물, 장애물 등 정적 맵 정보 저장
   - JSON 타입으로 유연한 데이터 구조 지원
   ========================================================= */

CREATE TABLE map_data (
  id              BIGINT NOT NULL AUTO_INCREMENT COMMENT '맵 데이터 ID',
  map_id          VARCHAR(50) NOT NULL COMMENT '맵 식별자',
  name            VARCHAR(100) NULL COMMENT '맵 이름',
  waypoints       JSON NULL COMMENT '웨이포인트 배열 (JSON)',
  buildings       JSON NULL COMMENT '건물/장애물 배열 (JSON)',
  obstacles       JSON NULL COMMENT '동적 장애물 배열 (JSON)',
  roads           JSON NULL COMMENT '도로 경로 배열 (JSON)',
  zones           JSON NULL COMMENT '작업 구역 배열 (JSON)',
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정 시간',
  PRIMARY KEY (id),
  UNIQUE KEY uk_map_id (map_id),
  INDEX idx_md_map_id (map_id)
) ENGINE=InnoDB COMMENT='맵 데이터';


/* =========================================================
   9) SensorStatus (센서 상태)
   - LIDAR, Camera, GPS, IMU 등 센서 실시간 상태 저장
   ========================================================= */

CREATE TABLE sensor_status (
  id              BIGINT NOT NULL AUTO_INCREMENT COMMENT '센서 상태 ID',
  vehicle_id      VARCHAR(50) NOT NULL COMMENT '차량 ID',
  sensor_name     VARCHAR(50) NOT NULL COMMENT '센서 이름 (LIDAR, Camera, GPS, IMU)',
  sensor_type     VARCHAR(50) NULL COMMENT '센서 유형',
  status          VARCHAR(20) NOT NULL DEFAULT 'ok' COMMENT '상태 (ok, warning, error, offline)',
  health          INT NULL DEFAULT 100 COMMENT '센서 상태 (0-100%)',
  value           VARCHAR(200) NULL COMMENT '센서 값 또는 설명',
  data            JSON NULL COMMENT '센서 상세 데이터 (JSON)',
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '마지막 업데이트',
  PRIMARY KEY (id),
  INDEX idx_ss_vehicle_id (vehicle_id),
  INDEX idx_ss_vehicle_sensor (vehicle_id, sensor_name),
  INDEX idx_ss_updated_at (updated_at)
) ENGINE=InnoDB COMMENT='센서 상태';

ALTER TABLE vehicle_position
  ADD CONSTRAINT chk_vp_battery CHECK (battery BETWEEN 0 AND 100);

ALTER TABLE sensor_status
  ADD CONSTRAINT chk_ss_health CHECK (health IS NULL OR (health BETWEEN 0 AND 100));


/* =========================================================
   10) 초기 데이터 삽입 (맵 데이터, 차량 위치, 센서 상태)
   ========================================================= */

-- 기본 맵 데이터 삽입
INSERT INTO map_data (map_id, name, waypoints, buildings, obstacles, roads, zones) VALUES (
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
  '[]',
  '[]',
  '[]'
);

-- 기본 차량 위치 삽입
INSERT INTO vehicle_position (vehicle_id, x, y, angle, speed, battery, mode) VALUES
  ('AGV-001', 450.0, 350.0, 0, 0, 100, 'IDLE');

-- 기본 센서 상태 삽입
INSERT INTO sensor_status (vehicle_id, sensor_name, sensor_type, status, health, value) VALUES
  ('AGV-001', 'LIDAR', 'lidar', 'ok', 100, '정상 (360°)'),
  ('AGV-001', 'Camera', 'rgb_camera', 'ok', 100, '정상 (1080p)'),
  ('AGV-001', 'GPS', 'gnss', 'ok', 95, '정확도 ±2m'),
  ('AGV-001', 'IMU', 'inertial', 'ok', 100, '정상');
