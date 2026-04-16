# 📦 AUTOBOX — 스마트 물류 자동 분류 시스템

> | 6인 팀 | 2026.01 ~ 2026.02

OCR로 운송장을 인식하고, 자율주행 RC카가 목적지 구역으로 박스를 자동 분류하는 물류 자동화 시스템입니다.  
Jetson Orin Nano + YPLIDAR X4로 구성된 자율주행 차량이 SLAM 지도 기반으로 주행하며, ArUco 마커를 통해 정밀 후진 주차를 수행합니다.

---

## 🏗️ 시스템 구성

```
┌─────────────────┐     TCP Socket     ┌──────────────────────┐
│  Raspberry Pi 5 │◄──────────────────►│   Jetson Orin Nano   │
│  컨베이어 제어    │                    │  ROS2 자율주행 + OCR  │
│  MQTT 게이트웨이  │                    │  YPLIDAR X4          │
└────────┬────────┘                    └──────────────────────┘
         │ TCP Socket
         ▼
┌─────────────────┐    REST / WebSocket    ┌──────────────────┐
│  Backend Server │◄──────────────────────►│  Web Dashboard   │
│ FastAPI + MySQL │                        │ Vue + TypeScript │
└─────────────────┘                        └──────────────────┘
```

| 구성요소 | 역할 |
|---|---|
| **Jetson Orin Nano** | ROS2 자율주행, OCR 기반 목적지 인식, ArUco 후진 주차 |
| **Raspberry Pi 5** | 컨베이어 벨트 제어, 서보 모터 제어, 서버-차량 게이트웨이 |
| **Backend (FastAPI)** | 작업 오케스트레이션, 운송장 상태 관리, DB 연동 |
| **Frontend (Vue)** | 실시간 물류 모니터링 대시보드, WebSocket 상태 반영 |

---

## ⚙️ 기술 스택

| 영역 | 기술 |
|---|---|
| **자율주행** | ROS2 Humble, Nav2, SLAM Toolbox, AMCL, TEB Local Planner |
| **센서** | YPLIDAR X4, rf2o LiDAR Odometry |
| **임베디드** | C++, Python, Jetson Orin Nano, Raspberry Pi 5 |
| **AI** | OCR (운송장 인식), ArUco 마커 검출 |
| **백엔드** | FastAPI, MySQL |
| **프론트엔드** | Vue 3, TypeScript, WebSocket |
| **인프라** | Docker, GitLab CI/CD, MQTT |

---

## 🚗 자율주행 파이프라인

```
[SLAM 매핑]  →  [지도 저장]  →  [AMCL 위치 추정]
                                       │
              [OCR 목적지 인식]  ──►  [Nav2 Goal 전송]
                                       │
                                [경로 계획 (A*)]
                                       │
                         [TEB Local Planner 주행]
                         (allow_reversing: true)
                                       │
                         [ArUco 마커 정밀 도킹]
                                       │
                              [박스 하차 → 복귀]
```

### 주요 구현 사항 (한승현 담당)

**ROS2 인프라 구축**
- YPLIDAR X4 드라이버 연동 및 `/scan` 토픽 발행, TF 좌표계 구성
- SLAM Toolbox로 실내 지도 생성, AMCL로 운영 중 실시간 위치 추정
- `bringup` 패키지 구성으로 전체 스택 단일 launch 실행
- LiDAR 좌표계 방향 오설정 문제 → TF 방향 검증 프로세스 정립

**Nav2 자율주행 구현**
- RC카 구조에 맞게 TEB Local Planner 적용 (`allow_reversing: true`)
- Static Costmap(지도) + Obstacle Layer(LiDAR 실시간) + Inflation Layer 조합으로 충돌 방지
- Global Planner(A*)로 전체 경로 계산, 장애물 발생 시 Local Costmap 갱신 후 재계획
- RC카 제자리 회전 불가로 인한 oscillation 문제 → 경로 재계획 주기 및 회전 반경 파라미터 튜닝으로 해결
- 라이다 오도메트리 정지 시 누적 오차 문제 → 도착 시점 좌표 저장 후 재출발 시 갱신하는 방식으로 해결

---

## 📁 레포지토리 구조

```
AUTOBOX/
├── embedded/       # ROS2 자율주행 (Jetson Orin Nano)
│   ├── bringup/    # 전체 스택 launch 패키지
│   ├── navigation/ # Nav2 파라미터 및 주행 노드
│   └── slam/       # SLAM Toolbox 설정
├── ai/             # OCR 및 ArUco 마커 처리
├── backend/        # FastAPI 서버
├── frontend/       # Vue 대시보드
├── docs/           # 시스템 구조도, ERD, API 명세
├── rebuild.sh      # 전체 재빌드 스크립트
└── .gitlab-ci.yml  # CI/CD 파이프라인
```

---

## 🔄 시스템 동작 흐름

1. 컨베이어 벨트에 박스 진입 → 카메라로 운송장 OCR 인식
2. 인식된 목적지 정보를 자율주행 차량에 전달
3. 차량이 SLAM 지도 기반으로 목적지 구역까지 자율 주행
4. ArUco 마커로 컨베이어 도킹 위치에 정밀 후진 주차
5. 박스 하차 완료 → 서버에 상태 보고 → 컨베이어로 복귀
6. 웹 대시보드에서 전체 물류 흐름 실시간 모니터링

---

## 👥 팀 구성 및 역할

| 이름 | 담당 |
|---|---|
| 한승현 | ROS2 인프라 구축, Nav2 자율주행 |
| 그 외 5인 | OCR, 컨베이어 제어, 백엔드, 프론트엔드 |

---

## 🏆 성과

- **삼성전자 우수상** 수상 (SSAFY 14기 AIoT 공통 프로젝트)
- 반 내 발표 시연에서 안정적인 자율주행 시연 성공

---