/* =========================================================
   AutoBox - Workbench 전체 조회용 SQL Pack
   ========================================================= */

USE S14P11A403;

/* ---------------------------
   0) 테이블 목록 / row count
---------------------------- */

-- 테이블 목록
SHOW TABLES;

-- 테이블별 row count(대략) : InnoDB는 정확치 않을 수 있음(추정치)
SELECT
  table_name,
  table_rows,
  ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY table_name;


/* ---------------------------
   1) logistics_item 전체/요약
---------------------------- */

-- 전체(최신 순)
SELECT *
FROM logistics_item
ORDER BY created_at DESC
LIMIT 500;

-- 상태별 건수
SELECT status, COUNT(*) AS cnt
FROM logistics_item
GROUP BY status
ORDER BY cnt DESC;

-- 목적지(region_id)별 건수
SELECT destination, COUNT(*) AS cnt
FROM logistics_item
GROUP BY destination
ORDER BY cnt DESC;

-- 최근 24시간 처리량(시간대별)
SELECT DATE_FORMAT(created_at, '%Y-%m-%d %H:00:00') AS hour_bucket,
       COUNT(*) AS created_cnt
FROM logistics_item
WHERE created_at >= NOW() - INTERVAL 1 DAY
GROUP BY hour_bucket
ORDER BY hour_bucket;


/* ---------------------------
   2) scan_log 전체/요약 + "최신 스캔" 조인
---------------------------- */

-- scan_log 전체(최신 순)
SELECT *
FROM scan_log
ORDER BY scanned_at DESC, id DESC
LIMIT 500;

-- 최근 스캔 50개(운송장/카메라/인식결과)
SELECT
  id, tracking_number, camera_id, detected_destination, confidence_score, scanned_at
FROM scan_log
ORDER BY scanned_at DESC, id DESC
LIMIT 50;

-- 카메라별 스캔 건수
SELECT camera_id, COUNT(*) AS cnt
FROM scan_log
GROUP BY camera_id
ORDER BY cnt DESC;

-- 운송장별 "최신 스캔 1개" 추출 (중요)
-- idx_sl_tracking_scanned 인덱스 활용 가능
WITH latest AS (
  SELECT
    tracking_number,
    MAX(scanned_at) AS max_scanned_at
  FROM scan_log
  GROUP BY tracking_number
)
SELECT
  sl.*
FROM scan_log sl
JOIN latest l
  ON l.tracking_number = sl.tracking_number
 AND l.max_scanned_at = sl.scanned_at
ORDER BY sl.scanned_at DESC, sl.id DESC
LIMIT 500;

-- 운송장 + 최신 스캔 + 처리시간(초)까지 한 번에 보기 (대시보드 핵심 뷰)
-- (completed_at이 있으면 completed_at-created_at, 없으면 NULL)
WITH latest_scan AS (
  SELECT sl.*
  FROM scan_log sl
  JOIN (
    SELECT tracking_number, MAX(scanned_at) AS max_scanned_at
    FROM scan_log
    GROUP BY tracking_number
  ) t
    ON t.tracking_number = sl.tracking_number
   AND t.max_scanned_at = sl.scanned_at
)
SELECT
  wm.waybill_id,
  li.tracking_number,
  li.destination,
  li.status,
  li.created_at,
  li.completed_at,
  CASE
    WHEN li.completed_at IS NULL THEN NULL
    ELSE TIMESTAMPDIFF(SECOND, li.created_at, li.completed_at)
  END AS process_time_sec,
  ls.camera_id AS latest_camera_id,
  ls.detected_destination AS latest_detected_destination,
  ls.confidence_score AS latest_confidence_score,
  ls.scanned_at AS latest_scanned_at
FROM logistics_item li
LEFT JOIN waybill_map wm
  ON wm.tracking_number = li.tracking_number
LEFT JOIN latest_scan ls
  ON ls.tracking_number = li.tracking_number
ORDER BY li.created_at DESC
LIMIT 500;


/* ---------------------------
   3) waybill_map 전체/검증
---------------------------- */

SELECT *
FROM waybill_map
ORDER BY waybill_id DESC
LIMIT 500;

-- 매핑 누락/고아 데이터 점검
-- 1) 매핑은 있는데 logistics_item이 없는 경우(정상이라면 0건)
SELECT wm.*
FROM waybill_map wm
LEFT JOIN logistics_item li
  ON li.tracking_number = wm.tracking_number
WHERE li.tracking_number IS NULL;

-- 2) logistics_item은 있는데 waybill_id가 없는 경우(허용 가능)
SELECT li.tracking_number
FROM logistics_item li
LEFT JOIN waybill_map wm
  ON wm.tracking_number = li.tracking_number
WHERE wm.waybill_id IS NULL
ORDER BY li.created_at DESC
LIMIT 200;


/* ---------------------------
   4) device_status 전체/정렬
---------------------------- */

SELECT *
FROM device_status
ORDER BY last_heartbeat DESC
LIMIT 200;

-- 연결 상태별
SELECT is_connected, COUNT(*) AS cnt
FROM device_status
GROUP BY is_connected;


/* ---------------------------
   5) region / camera / alert
---------------------------- */

-- region
SELECT *
FROM region
ORDER BY is_active DESC, display_order ASC;

-- camera
SELECT *
FROM camera
ORDER BY status DESC, last_heartbeat DESC
LIMIT 200;

-- alert (미해결 우선)
SELECT *
FROM alert
ORDER BY is_resolved ASC, created_at DESC
LIMIT 500;

-- severity별
SELECT severity, COUNT(*) AS cnt
FROM alert
GROUP BY severity
ORDER BY cnt DESC;


/* ---------------------------
   6) vehicle_position / map_data / sensor_status
---------------------------- */

-- vehicle_position (최신순)
SELECT *
FROM vehicle_position
ORDER BY updated_at DESC, id DESC
LIMIT 500;

-- 차량별 "최신 위치 1개" 뽑기
WITH latest_vp AS (
  SELECT vehicle_id, MAX(updated_at) AS max_updated_at
  FROM vehicle_position
  GROUP BY vehicle_id
)
SELECT vp.*
FROM vehicle_position vp
JOIN latest_vp l
  ON l.vehicle_id = vp.vehicle_id
 AND l.max_updated_at = vp.updated_at
ORDER BY vp.updated_at DESC, vp.id DESC;

-- map_data
SELECT id, map_id, name, created_at, updated_at
FROM map_data
ORDER BY updated_at DESC
LIMIT 100;

-- map_data JSON 미리보기(waypoints만)
SELECT map_id, JSON_PRETTY(waypoints) AS waypoints_pretty
FROM map_data
WHERE map_id = 'default';

-- sensor_status (최신순)
SELECT *
FROM sensor_status
ORDER BY updated_at DESC, id DESC
LIMIT 500;

-- 차량별/센서별 최신상태
WITH latest_ss AS (
  SELECT vehicle_id, sensor_name, MAX(updated_at) AS max_updated_at
  FROM sensor_status
  GROUP BY vehicle_id, sensor_name
)
SELECT ss.*
FROM sensor_status ss
JOIN latest_ss l
  ON l.vehicle_id = ss.vehicle_id
 AND l.sensor_name = ss.sensor_name
 AND l.max_updated_at = ss.updated_at
ORDER BY ss.vehicle_id, ss.sensor_name;


/* ---------------------------
   7) "전체 통합 대시보드" 한 번에 보기 (요약)
---------------------------- */

-- 7-1) 운송장 상태 요약
SELECT
  COUNT(*) AS total_items,
  SUM(status='READY')     AS ready_cnt,
  SUM(status='MOVING')    AS moving_cnt,
  SUM(status='COMPLETED') AS completed_cnt,
  SUM(status='ERROR')     AS error_cnt
FROM logistics_item;

-- 7-2) 최근 10개 운송장 + 최신 스캔
WITH latest_scan AS (
  SELECT sl.*
  FROM scan_log sl
  JOIN (
    SELECT tracking_number, MAX(scanned_at) AS max_scanned_at
    FROM scan_log
    GROUP BY tracking_number
  ) t
    ON t.tracking_number = sl.tracking_number
   AND t.max_scanned_at = sl.scanned_at
)
SELECT
  li.tracking_number, li.destination, li.status, li.created_at,
  ls.camera_id, ls.detected_destination, ls.confidence_score, ls.scanned_at
FROM logistics_item li
LEFT JOIN latest_scan ls
  ON ls.tracking_number = li.tracking_number
ORDER BY li.created_at DESC
LIMIT 10;

-- 7-3) 장치 상태 요약(연결/배터리)
SELECT
  COUNT(*) AS total_devices,
  SUM(is_connected=1) AS connected_devices,
  ROUND(AVG(battery_level), 1) AS avg_battery
FROM device_status;

-- 7-4) 미해결 알림 TOP 20
SELECT
  alert_id, severity, alert_type, title, source_type, source_id, created_at
FROM alert
WHERE is_resolved = 0
ORDER BY severity DESC, created_at DESC
LIMIT 20;
