# 오토박스 API 명세서

## 0. 개요

| 항목 | 내용 |
| --- | --- |
| 서버 | FastAPI |
| Base URL | `http://localhost:8000/api/v1` |
| 인증 | 없음 (내부 시스템) |
| 응답 형식 | JSON |
| 문서 버전 | **1.2** |
| 최종 수정일 | 2026-01-26 |

---

## 1. 공통 응답 형식

### 1.1 성공 응답

```json
{
  "success": true,
  "data": { },
  "message": "처리 완료"
}

```

### 1.2 실패 응답

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}

```

---

## 2. 공통 규칙 (중요)

### 2.1 식별자 규칙

| 필드 | 설명 |
| --- | --- |
| `waybill_id` | 내부 API 식별자 (숫자, URL 경로용) |
| `tracking_number` | 실제 운송장 번호 (업무 도메인 키) |

> 모든 운송장 관련 API Response에는 두 필드 모두 포함한다.
> 

---

### 2.2 상태(status) 표준값

API 외부 표준 상태는 아래 **4개만 사용**한다.

| 상태 | 의미 |
| --- | --- |
| `READY` | 스캔 시작 ~ OCR 인식 완료 |
| `MOVING` | 분류 차량 이동 중 |
| `COMPLETED` | 분류 완료 |
| `ERROR` | 오류 발생 |

> scanning, recognized 등은 내부 로그용 이벤트이며
> 
> 
> **API Response의 status 값으로는 사용하지 않는다.**
> 

---

### 2.3 시간 필드 규칙

| 필드 | 의미 |
| --- | --- |
| `created_at` | 운송장 생성 시각 |
| `updated_at` | 상태 변경 시각 |
| `completed_at` | 분류 완료 시각 |
| `scanned_at` | OCR/카메라 인식 이벤트 시각 |

---

## 3. 운송장 API

---

### 3.1 운송장 스캔 시작 (WB-001)

새로운 운송장 레코드를 생성한다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/waybills/scan` |

**Request Body**

```json
{
  "camera_id": "cam-capture"
}

```

**Response**

```json
{
  "success": true,
  "data": {
    "waybill_id": 1,
    "tracking_number": "TRK-2024-001",
    "status": "READY",
    "created_at": "2024-01-15T14:20:00"
  }
}

```

---

### 3.2 OCR 인식 결과 저장 (WB-002)

AI 인식 결과를 저장한다.

| 항목 | 내용 |
| --- | --- |
| Method | `PUT` |
| URL | `/waybills/{waybill_id}/recognition` |

**Request Body**

```json
{
  "recognized_text": "서울-A",
  "destination": "seoul-a",
  "confidence_score": 98.5,
  "camera_id": "cam-capture"
}

```

**Response**

```json
{
  "success": true,
  "data": {
    "waybill_id": 1,
    "tracking_number": "TRK-2024-001",
    "status": "READY",
    "destination": "seoul-a",
    "confidence_score": 98.5,
    "scanned_at": "2024-01-15T14:20:05"
  }
}

```

---

### 3.3 분류 시작 (WB-003)

차량이 박스를 적재하고 이동을 시작한다.

| 항목 | 내용 |
| --- | --- |
| Method | `PUT` |
| URL | `/waybills/{waybill_id}/start-sorting` |

**Response**

```json
{
  "success": true,
  "data": {
    "waybill_id": 1,
    "tracking_number": "TRK-2024-001",
    "status": "MOVING",
    "updated_at": "2024-01-15T14:20:10"
  }
}

```

---

### 3.4 분류 완료 (WB-004)

목적지 도착 후 하역 완료 처리한다.

| 항목 | 내용 |
| --- | --- |
| Method | `PUT` |
| URL | `/waybills/{waybill_id}/complete` |

**Response**

```json
{
  "success": true,
  "data": {
    "waybill_id": 1,
    "tracking_number": "TRK-2024-001",
    "status": "COMPLETED",
    "completed_at": "2024-01-15T14:25:30",
    "process_time_sec": 330
  }
}

```

---

### 3.5 오류 처리 (WB-005)

인식 실패 시 오류 상태로 전환한다.

| 항목 | 내용 |
| --- | --- |
| Method | `PUT` |
| URL | `/waybills/{waybill_id}/error` |

**Request Body**

```json
{
  "error_reason": "인식 신뢰도 부족 (45%)"
}

```

**Response**

```json
{
  "success": true,
  "data": {
    "waybill_id": 1,
    "tracking_number": "TRK-2024-001",
    "status": "ERROR",
    "alert_id": 5,
    "updated_at": "2024-01-15T14:23:01"
  }
}

```

---

### 3.6 운송장 목록 조회 (WB-006)

대시보드 테이블에 표시할 운송장 목록을 조회한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/waybills` |

**Query Parameters**

| 파라미터 | 설명 |
| --- | --- |
| date | 조회 날짜 (YYYY-MM-DD) |
| status | READY / MOVING / COMPLETED / ERROR |
| region | destination 필터 |
| page | 페이지 번호 |
| size | 페이지 크기 |

**Response**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "waybill_id": 1,
        "tracking_number": "TRK-2024-001",
        "destination": "seoul-a",
        "status": "COMPLETED",
        "created_at": "2024-01-15T14:15:00",
        "completed_at": "2024-01-15T14:20:05",
        "process_time_sec": 305
      }
    ],
    "total": 50,
    "page": 1,
    "size": 20,
    "total_pages": 3
  }
}

```

---

### 3.7 운송장 상세 조회 (WB-007)

특정 운송장의 상세 정보를 조회한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/waybills/{waybill_id}` |

**Response**

```json
{
  "success": true,
  "data": {
    "item": {
      "waybill_id": 1,
      "tracking_number": "TRK-2024-001",
      "destination": "seoul-a",
      "status": "COMPLETED",
      "created_at": "2024-01-15T14:15:00",
      "completed_at": "2024-01-15T14:20:05"
    },
    "scan_logs": [
      {
        "camera_id": "cam-capture",
        "detected_destination": "seoul-a",
        "confidence_score": 98.5,
        "scanned_at": "2024-01-15T14:15:05"
      }
    ]
  }
}

```

---

## 4. 구역 API

### 4.1 구역 목록 조회 (RG-001)

```json
GET /regions

```

```json
{
  "success": true,
  "data": [
    {
      "region_id": "seoul-a",
      "region_name": "서울-A",
      "region_detail": "마포",
      "display_order": 1,
      "is_active": true
    }
  ]
}

```

---

## 5. 시스템 상태 API

### 5.1 시스템 상태 조회 (SYS-001)

```json
GET /system/status

```

```json
{
  "success": true,
  "data": {
    "device_id": "ROBOT_01",
    "battery_level": 82,
    "is_connected": true,
    "operation_status": "TRANSPORT",
    "last_heartbeat": "2024-01-15T14:30:00"
  }
}

```

### 5.2 시스템 상태 업데이트 (SYS-002)

```json
PUT /system/status

```

```json
{
  "device_id": "ROBOT_01",
  "battery_level": 80,
  "is_connected": true,
  "operation_status": "TRANSPORT"
}

```

---

## 6. 알림 API

- 알림 생성: `POST /alerts`
- 알림 목록 조회: `GET /alerts`
- 알림 해결 처리: `PATCH /alerts/{alert_id}/resolve`

> source_type / source_id 폴리모픽 구조 유지
> 

---

## 7. 통계 API

- `GET /stats/regions`
- `GET /stats/daily`
- `GET /stats/export`

> 상태 기준은 READY / MOVING / COMPLETED / ERROR
> 

---

## 8. 카메라 인식 정보 API

### 8.1 최신 인식 정보 조회 (CAM-001)

```json
{
  "success": true,
  "data": {
    "scan_log": {
      "tracking_number": "WB-8842-99",
      "camera_id": "CAM:01",
      "detected_destination": "seoul-a",
      "confidence_score": 98,
      "scanned_at": "2024-01-15T14:35:00"
    }
  }
}

```

---

## 9. WebSocket API

### 9.1 대시보드 실시간 업데이트

**URL**

```
ws://localhost:8000/ws/dashboard
```

### waybill_update

```json
{
  "type": "waybill_update",
  "data": {
    "waybill_id": 10,
    "tracking_number": "TRK-2024-010",
    "status": "COMPLETED",
    "destination": "seoul-a"
  }
}
```

### system_status

```json
{
  "type": "system_status",
  "data": {
    "device_id": "ROBOT_01",
    "battery_level": 80,
    "is_connected": true,
    "operation_status": "TRANSPORT"
  }
}
```

### vehicle_position (신규)

```json
{
  "type": "vehicle_position",
  "data": {
    "vehicle_id": "AGV-001",
    "x": 450.0,
    "y": 350.0,
    "angle": 45.2,
    "speed": 12.5,
    "battery": 85,
    "mode": "AUTO",
    "timestamp": "2026-01-26T12:00:00"
  }
}
```

### sensor_status (신규)

```json
{
  "type": "sensor_status",
  "data": {
    "vehicle_id": "AGV-001",
    "sensor_name": "LIDAR",
    "status": "ok",
    "value": "정상 (360°)",
    "health": 100,
    "timestamp": "2026-01-26T12:00:00"
  }
}
```

### command_sent (신규)

```json
{
  "type": "command_sent",
  "data": {
    "command_id": "CMD-A1B2C3D4",
    "command_type": "box_count",
    "box_count": 10,
    "vehicle_id": "AGV-001",
    "timestamp": "2026-01-26T12:00:00"
  }
}
```

---

## 10. 차량/맵/센서 API (실시간 모니터링)

### 10.1 차량 위치 조회 (VH-001)

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/vehicle/position` |

**Query Parameters**

| 파라미터 | 설명 |
| --- | --- |
| vehicle_id | 차량 ID (선택, 미지정시 최신 데이터) |

**Response**

```json
{
  "success": true,
  "data": {
    "x": 450.0,
    "y": 350.0,
    "angle": 45.2,
    "speed": 12.5,
    "battery": 85,
    "mode": "AUTO",
    "timestamp": "2026-01-26T12:00:00"
  }
}
```

---

### 10.2 차량 위치 업데이트 (VH-002)

| 항목 | 내용 |
| --- | --- |
| Method | `PUT` |
| URL | `/vehicle/position` |

**Request Body**

```json
{
  "vehicle_id": "AGV-001",
  "x": 500.0,
  "y": 400.0,
  "angle": 90.0,
  "speed": 10.5,
  "battery": 80,
  "mode": "AUTO"
}
```

---

### 10.3 맵 데이터 조회 (MAP-001)

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/map/data` |

**Response**

```json
{
  "success": true,
  "data": {
    "map_id": "default",
    "waypoints": [
      { "id": 1, "label": "A", "x": 200, "y": 300, "color": "#10b981", "type": "pickup" },
      { "id": 2, "label": "B", "x": 500, "y": 200, "color": "#f59e0b", "type": "dropoff" }
    ],
    "buildings": [
      { "id": 1, "x": 150, "y": 150, "width": 100, "height": 80, "type": "building" }
    ],
    "obstacles": []
  }
}
```

---

### 10.4 센서 상태 조회 (SEN-001)

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/sensors/status` |

**Response**

```json
{
  "success": true,
  "data": {
    "sensors": [
      { "name": "LIDAR", "status": "ok", "value": "정상 (360°)", "health": 100 },
      { "name": "Camera", "status": "ok", "value": "정상 (1080p)", "health": 100 },
      { "name": "GPS", "status": "ok", "value": "정확도 ±2m", "health": 95 },
      { "name": "IMU", "status": "ok", "value": "정상", "health": 100 }
    ],
    "vehicle_id": "AGV-001",
    "timestamp": "2026-01-26T12:00:00"
  }
}
```

---

## 11. 명령 전송 API (MQTT 연동)

### 11.1 박스 개수 명령 전송 (CMD-001)

프론트엔드에서 라즈베리파이로 박스 개수를 전송합니다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/vehicle/command/box-count` |

**Request Body**

```json
{
  "box_count": 10,
  "vehicle_id": "AGV-001",
  "priority": "normal"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "command_id": "CMD-A1B2C3D4",
    "box_count": 10,
    "vehicle_id": "AGV-001",
    "status": "sent",
    "sent_at": "2026-01-26T12:00:00"
  },
  "message": "박스 개수 10개 명령이 전송되었습니다."
}
```

**MQTT 토픽**: `autobox/command/box-count`

---

### 11.2 차량 제어 명령 전송 (CMD-002)

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/vehicle/command` |

**Request Body**

```json
{
  "command": "start",
  "vehicle_id": "AGV-001",
  "parameters": {}
}
```

**허용 명령**: `start`, `stop`, `pause`, `resume`, `emergency_stop`, `reset`

**Response**

```json
{
  "success": true,
  "data": {
    "command_id": "CMD-E5F6G7H8",
    "command": "start",
    "vehicle_id": "AGV-001",
    "status": "sent",
    "sent_at": "2026-01-26T12:00:00"
  },
  "message": "'start' 명령이 전송되었습니다."
}
```

**MQTT 토픽**: `autobox/command/vehicle`

---

## 12. 에러 코드

| 코드 | 설명 |
| --- | --- |
| WAYBILL_NOT_FOUND | 운송장을 찾을 수 없음 |
| REGION_NOT_FOUND | 구역을 찾을 수 없음 |
| CAMERA_NOT_FOUND | 카메라를 찾을 수 없음 |
| ALERT_NOT_FOUND | 알림을 찾을 수 없음 |
| VEHICLE_NOT_FOUND | 차량을 찾을 수 없음 |
| INVALID_STATUS | 잘못된 상태 값 |
| INVALID_COMMAND | 허용되지 않는 명령 |
| DUPLICATE_WAYBILL_NO | 중복 운송장 번호 |
| INVALID_CONFIDENCE | 신뢰도 값 범위 오류 |
| MQTT_CONNECTION_ERROR | MQTT 연결 오류 |
| DATABASE_ERROR | 데이터베이스 오류 |