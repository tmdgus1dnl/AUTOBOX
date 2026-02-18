/**
 * 애플리케이션 전역 상수
 */

// 상태 매핑 (백엔드 → 프론트엔드)
export const STATUS_MAP = {
  READY: "대기 중",
  MOVING: "이동 중",
  COMPLETED: "완료",
  ERROR: "오류",
};

// 상태 우선순위 (정렬용)
export const STATUS_PRIORITY = {
  "이동 중": 1,
  "대기 중": 2,
  완료: 3,
  오류: 4,
};

// 지역 목록
export const CITIES = ["서울", "부산", "광주", "대전", "대구"];

// 필터 옵션
export const FILTER_OPTIONS = {
  regions: [
    { value: "전체", label: "지역: 전체" },
    { value: "서울", label: "서울" },
    { value: "부산", label: "부산" },
    { value: "광주", label: "광주" },
    { value: "대전", label: "대전" },
    { value: "대구", label: "대구" },
  ],
  statuses: [
    { value: "전체", label: "상태: 전체" },
    { value: "완료", label: "완료" },
    { value: "이동 중", label: "이동 중" },
    { value: "대기 중", label: "대기 중" },
  ],
};

// 차트 색상
export const CHART_COLORS = {
  completed: "#3b82f6", // 파란색 (지역 완료)
  totalCompleted: "#10b981", // 초록색 (전체 완료)
  pending: "#475569", // 회색 (미완료)
  grid: "#1e293b",
  text: "#94a3b8",
};

// 지역별 색상 (서울, 부산, 광주, 대전, 대구 순서)
export const REGION_COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"];

// 폴링 간격 (ms)
export const POLLING_INTERVALS = {
  dashboard: 3000, // 대시보드 데이터 갱신
  systemStatus: 5000, // 시스템 상태 갱신
  alerts: 10000, // 알림 갱신
};
