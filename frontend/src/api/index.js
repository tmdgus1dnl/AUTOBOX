import axios from "axios";
import {
  mockRegionStats,
  mockWaybills,
  mockDailyStats,
  mockAlerts,
  mockSystemStatus,
  mockCameras,
  mockRegions,
  mockLatestRecognition,
  mockWaybillDetail,
} from "./mockData";

// 목업 모드 확인 (환경변수 VITE_MOCK_MODE=true로 설정)
const isMockMode = import.meta.env.VITE_MOCK_MODE === "true";

// 콘솔에 현재 모드 표시
if (isMockMode) {
  console.log("🎭 목업 모드로 실행 중입니다. 백엔드 연결 없이 샘플 데이터가 표시됩니다.");
}

// 백엔드 주소 설정 (환경변수로 관리 - 배포 환경 대응)
// Docker 환경에서는 nginx 프록시를 통해 /api/v1로 접근
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// 목업 응답 딜레이 (실제 API처럼 느끼도록)
const mockDelay = (data, delay = 200) => {
  return new Promise((resolve) => setTimeout(() => resolve(data), delay));
};

// 1. 대시보드 통계 데이터 가져오기 (구역별 현황)
export const fetchDashboardStats = (dateStr) => {
  if (isMockMode) {
    return mockDelay(mockRegionStats);
  }
  return apiClient.get("/stats/regions", {
    params: { date: dateStr },
  });
};

// 2. 일별 처리 통계 가져오기
export const fetchDailyStats = (startDate, endDate) => {
  if (isMockMode) {
    return mockDelay(mockDailyStats);
  }
  return apiClient.get("/stats/daily", {
    params: { start_date: startDate, end_date: endDate },
  });
};

// 3. 시스템 상태 가져오기
export const fetchSystemStatus = () => {
  if (isMockMode) {
    // 목업에서 배터리 레벨을 랜덤하게 변동
    const mockData = { ...mockSystemStatus };
    mockData.data.data.battery_level = Math.min(
      100,
      Math.max(70, mockSystemStatus.data.data.battery_level + Math.floor(Math.random() * 5) - 2),
    );
    mockData.data.data.last_updated = new Date().toISOString();
    return mockDelay(mockData);
  }
  return apiClient.get("/system/status");
};

// 4. 운송장 목록 조회
export const fetchWaybills = (params = {}) => {
  if (isMockMode) {
    return mockDelay(mockWaybills);
  }
  return apiClient.get("/waybills", { params });
};

// 5. 운송장 상세 조회 (scan_logs 포함)
export const fetchWaybillDetail = (waybillId) => {
  if (isMockMode) {
    return mockDelay(mockWaybillDetail);
  }
  return apiClient.get(`/waybills/${waybillId}`);
};

// 5-1. 운송장 OCR 이미지 조회
export const fetchWaybillImage = (trackingNumber) => {
  return apiClient.get(`/waybills/${trackingNumber}/image`);
};

// 6. 알림 목록 조회
export const fetchAlerts = (params = {}) => {
  if (isMockMode) {
    return mockDelay(mockAlerts);
  }
  return apiClient.get("/alerts", { params });
};

// 7. 알림 해결 처리
export const resolveAlert = (alertId) => {
  if (isMockMode) {
    return mockDelay({ data: { success: true, message: "알림이 해결되었습니다." } });
  }
  return apiClient.patch(`/alerts/${alertId}/resolve`);
};

// 8. 구역 목록 조회
export const fetchRegions = () => {
  if (isMockMode) {
    return mockDelay(mockRegions);
  }
  return apiClient.get("/regions");
};

// 9. 카메라 목록 조회
export const fetchCameras = () => {
  if (isMockMode) {
    return mockDelay(mockCameras);
  }
  return apiClient.get("/cameras");
};

// 10. 최신 인식 정보 조회
export const fetchLatestRecognition = () => {
  if (isMockMode) {
    return mockDelay(mockLatestRecognition);
  }
  return apiClient.get("/recognition/latest");
};

// 11. 운송장 스캔 시작 (새 운송장 생성)
export const startWaybillScan = (cameraId = "cam-capture") => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        data: {
          waybill_id: `WB-MOCK-${Date.now()}`,
          status: "SCANNING",
        },
      },
    });
  }
  return apiClient.post("/waybills/scan", { camera_id: cameraId });
};

// 12. OCR 인식 결과 저장
export const saveRecognitionResult = (waybillId, data) => {
  if (isMockMode) {
    return mockDelay({ data: { success: true, waybill_id: waybillId } });
  }
  return apiClient.put(`/waybills/${waybillId}/recognition`, data);
};

// 13. 분류 시작
export const startSorting = (waybillId) => {
  if (isMockMode) {
    return mockDelay({ data: { success: true, status: "MOVING" } });
  }
  return apiClient.put(`/waybills/${waybillId}/start-sorting`);
};

// 14. 분류 완료
export const completeSorting = (waybillId) => {
  if (isMockMode) {
    return mockDelay({ data: { success: true, status: "COMPLETED" } });
  }
  return apiClient.put(`/waybills/${waybillId}/complete`);
};

// 15. 엑셀 다운로드 URL 생성
// 15. 엑셀 다운로드 URL 생성
export const getExportUrl = (params) => {
  if (isMockMode) {
    console.log("🎭 목업 모드: 엑셀 다운로드는 실제 백엔드 연결 시 사용 가능합니다.");
    return "#";
  }
  const baseUrl = import.meta.env.VITE_API_URL || "/api/v1";

  // 기존 하위 호환성 (params가 문자열이면 date로 취급)
  if (typeof params === "string") {
    return `${baseUrl}/stats/export?date=${params}`;
  }

  // 객체인 경우 쿼리 스트링 빌드
  if (params) {
    const query = new URLSearchParams();
    if (params.date) query.append("date", params.date);
    if (params.startDate) query.append("start_date", params.startDate);
    if (params.endDate) query.append("end_date", params.endDate);
    const queryString = query.toString();
    return `${baseUrl}/stats/export${queryString ? `?${queryString}` : ""}`;
  }

  // 파라미터 없으면 전체 다운로드
  return `${baseUrl}/stats/export`;
};

// 16. 차량 위치 정보 조회
export const fetchVehiclePosition = () => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        data: {
          x: Math.random() * 800 + 100,
          y: Math.random() * 600 + 100,
          angle: Math.random() * 360,
          speed: (Math.random() * 15).toFixed(1),
          battery: 85,
          mode: "AUTO",
          timestamp: new Date().toISOString(),
        },
      },
    });
  }
  return apiClient.get("/vehicle/position");
};

// 16-1. RC 상태 조회 (실시간 로그 파일에서 읽기)
export const fetchRcState = () => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        connected: true,
        data: {
          device_id: "rc1",
          speed: Math.random() * 2,
          state: "IDLE",
          x: Math.random() * 10,
          y: Math.random() * 10,
          theta: Math.random() * 360,
          path: "",
          remain_dist: Math.random() * 5,
          remain_time: Math.floor(Math.random() * 30),
        },
      },
    });
  }
  return apiClient.get("/vehicle/rc-state");
};

// 17. 맵 데이터 조회 (경로, 장애물, waypoints 등)
export const fetchMapData = () => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        data: {
          waypoints: [
            { id: 1, label: "A", x: 200, y: 300, color: "#10b981" },
            { id: 2, label: "B", x: 500, y: 200, color: "#f59e0b" },
            { id: 3, label: "C", x: 750, y: 300, color: "#ef4444" },
            { id: 4, label: "D", x: 500, y: 600, color: "#3b82f6" },
          ],
          obstacles: [],
          buildings: [
            { id: 1, x: 150, y: 150, width: 100, height: 80, type: "building" },
            { id: 2, x: 650, y: 150, width: 120, height: 100, type: "building" },
            { id: 3, x: 150, y: 450, width: 90, height: 110, type: "building" },
            { id: 4, x: 700, y: 450, width: 100, height: 90, type: "building" },
          ],
        },
      },
    });
  }
  return apiClient.get("/map/data");
};

// 18. 센서 상태 조회
export const fetchSensorStatus = () => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        data: {
          sensors: [
            { name: "LIDAR", status: "ok", value: "정상 (360°)" },
            { name: "Camera", status: "ok", value: "정상 (1080p)" },
            { name: "GPS", status: "ok", value: "정확도 ±2m" },
            { name: "IMU", status: "ok", value: "정상" },
          ],
        },
      },
    });
  }
  return apiClient.get("/sensors/status");
};

// ============== 라즈베리파이 명령 전송 API ==============

// 19. 박스 개수 명령 전송 (라즈베리파이로 MQTT 전송)
export const sendBoxCountCommand = (boxCount, vehicleId = "AGV-001", priority = "normal") => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        data: {
          command_id: `CMD-MOCK-${Date.now()}`,
          box_count: boxCount,
          vehicle_id: vehicleId,
          status: "sent",
          sent_at: new Date().toISOString(),
        },
        message: `박스 개수 ${boxCount}개 명령이 전송되었습니다.`,
      },
    });
  }
  return apiClient.post("/vehicle/command/box-count", {
    box_count: boxCount,
    vehicle_id: vehicleId,
    priority: priority,
  });
};

// 20. 차량 제어 명령 전송 (start, stop, pause, resume, emergency_stop)
export const sendVehicleCommand = (command, vehicleId = "AGV-001", parameters = {}) => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        data: {
          command_id: `CMD-MOCK-${Date.now()}`,
          command: command,
          vehicle_id: vehicleId,
          status: "sent",
          sent_at: new Date().toISOString(),
        },
        message: `'${command}' 명령이 전송되었습니다.`,
      },
    });
  }
  return apiClient.post("/vehicle/command", {
    command: command,
    vehicle_id: vehicleId,
    parameters: parameters,
  });
};

// 21. 물류 데이터 초기화 (모든 운송장 삭제)
export const resetAllWaybills = () => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        message: "목업 모드에서는 실제 데이터가 삭제되지 않습니다.",
        deleted_count: 0,
      },
    });
  }
  return apiClient.delete("/waybills/reset");
};

// 22. OCR 결과 조회
export const fetchOcrResults = (limit = 20) => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        data: {
          items: [],
          total: 0,
        },
      },
    });
  }
  return apiClient.get("/ocr/results", { params: { limit } });
};

// 23. OCR 서비스 상태 조회
export const fetchOcrStatus = () => {
  if (isMockMode) {
    return mockDelay({
      data: {
        success: true,
        data: {
          enabled: false,
          watch_directory: "./data",
          api_url: "",
          results_count: 0,
        },
      },
    });
  }
  return apiClient.get("/ocr/status");
};

// 목업 모드 여부 내보내기 (UI에서 표시용)
export const getMockMode = () => isMockMode;

// API 클라이언트 내보내기 (커스텀 요청용)
export default apiClient;
