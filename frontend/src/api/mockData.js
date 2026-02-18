/**
 * 목업 데이터 - 백엔드 없이 프론트엔드 테스트용
 */

// 현재 날짜 기준으로 생성
const today = new Date().toISOString().split('T')[0]

// 구역별 통계 목업 데이터
export const mockRegionStats = {
  data: {
    data: [
      { region_name: '서울', completed: 67, ready: 0, moving: 0, error: 0 },
      { region_name: '부산', completed: 59, ready: 0, moving: 0, error: 0 },
      { region_name: '광주', completed: 40, ready: 0, moving: 0, error: 0 },
      { region_name: '대전', completed: 49, ready: 0, moving: 0, error: 0 },
      { region_name: '대구', completed: 55, ready: 0, moving: 0, error: 0 }
    ]
  }
}

// 운송장 목록 목업 데이터
export const mockWaybills = {
  data: {
    data: {
      items: [
        {
          waybill_id: 'WB-001',
          tracking_number: '123456789012',
          destination: '서울',
          status: 'COMPLETED',
          created_at: `${today}T09:15:32`,
          completed_at: `${today}T09:16:45`,
          process_time_sec: 73,
          confidence_score: 98.5
        },
        {
          waybill_id: 'WB-002',
          tracking_number: '234567890123',
          destination: '부산',
          status: 'COMPLETED',
          created_at: `${today}T09:18:22`,
          completed_at: `${today}T09:19:35`,
          process_time_sec: 73,
          confidence_score: 95.2
        },
        {
          waybill_id: 'WB-003',
          tracking_number: '345678901234',
          destination: '대전',
          status: 'COMPLETED',
          created_at: `${today}T09:20:11`,
          completed_at: `${today}T09:21:24`,
          process_time_sec: 73,
          confidence_score: 97.8
        },
        {
          waybill_id: 'WB-004',
          tracking_number: '456789012345',
          destination: '광주',
          status: 'COMPLETED',
          created_at: `${today}T09:22:05`,
          completed_at: `${today}T09:23:18`,
          process_time_sec: 73,
          confidence_score: 99.1
        },
        {
          waybill_id: 'WB-005',
          tracking_number: '567890123456',
          destination: '대구',
          status: 'COMPLETED',
          created_at: `${today}T09:25:44`,
          completed_at: `${today}T09:26:57`,
          process_time_sec: 73,
          confidence_score: 97.2
        },
        {
          waybill_id: 'WB-006',
          tracking_number: '678901234567',
          destination: '서울',
          status: 'COMPLETED',
          created_at: `${today}T09:28:33`,
          completed_at: `${today}T09:29:48`,
          process_time_sec: 75,
          confidence_score: 96.8
        },
        {
          waybill_id: 'WB-007',
          tracking_number: '789012345678',
          destination: '부산',
          status: 'COMPLETED',
          created_at: `${today}T09:31:22`,
          completed_at: `${today}T09:32:35`,
          process_time_sec: 73,
          confidence_score: 94.5
        },
        {
          waybill_id: 'WB-008',
          tracking_number: '890123456789',
          destination: '대전',
          status: 'COMPLETED',
          created_at: `${today}T09:34:15`,
          completed_at: `${today}T09:35:28`,
          process_time_sec: 73,
          confidence_score: 98.2
        },
        {
          waybill_id: 'WB-009',
          tracking_number: '901234567890',
          destination: '광주',
          status: 'COMPLETED',
          created_at: `${today}T09:37:08`,
          completed_at: `${today}T09:38:21`,
          process_time_sec: 73,
          confidence_score: 97.5
        },
        {
          waybill_id: 'WB-010',
          tracking_number: '012345678901',
          destination: '대구',
          status: 'COMPLETED',
          created_at: `${today}T09:40:01`,
          completed_at: `${today}T09:41:14`,
          process_time_sec: 73,
          confidence_score: 99.3
        }
      ],
      total: 270,
      page: 1,
      size: 100
    }
  }
}

// 일별 통계 목업 데이터
export const mockDailyStats = {
  data: {
    data: [
      {
        date: today,
        total_count: 270,
        completed_count: 270,
        error_count: 0,
        avg_process_time_sec: 73,
        success_rate: 100
      }
    ]
  }
}

// 알림 목업 데이터
export const mockAlerts = {
  data: {
    data: {
      items: [
        {
          alert_id: 'ALT-001',
          alert_type: 'OCR_ERROR',
          message: '운송장 인식 실패: 567890123456',
          waybill_id: 'WB-005',
          tracking_number: '567890123456',
          created_at: `${today}T09:25:50`,
          resolved: false,
          severity: 'HIGH'
        },
        {
          alert_id: 'ALT-002',
          alert_type: 'LOW_CONFIDENCE',
          message: '낮은 신뢰도 인식: 234567890123 (85.2%)',
          waybill_id: 'WB-002',
          tracking_number: '234567890123',
          created_at: `${today}T09:18:30`,
          resolved: false,
          severity: 'MEDIUM'
        },
        {
          alert_id: 'ALT-003',
          alert_type: 'SYSTEM_WARNING',
          message: '카메라 CAM:02 연결 불안정',
          waybill_id: null,
          tracking_number: null,
          created_at: `${today}T08:45:22`,
          resolved: false,
          severity: 'LOW'
        }
      ],
      total: 3
    }
  }
}

// 시스템 상태 목업 데이터
export const mockSystemStatus = {
  data: {
    data: {
      battery_level: 85,
      is_connected: true,
      camera_status: 'ACTIVE',
      ocr_status: 'RUNNING',
      conveyor_status: 'RUNNING',
      last_updated: new Date().toISOString()
    }
  }
}

// 카메라 목록 목업 데이터
export const mockCameras = {
  data: {
    data: [
      { camera_id: 'CAM-01', name: '메인 카메라', status: 'ACTIVE', location: '컨베이어 입구' },
      { camera_id: 'CAM-02', name: '보조 카메라', status: 'ACTIVE', location: '분류 영역' }
    ]
  }
}

// 구역 목록 목업 데이터
export const mockRegions = {
  data: {
    data: [
      { region_id: 'R-001', name: '서울', code: 'SEL', color: '#3b82f6' },
      { region_id: 'R-002', name: '부산', code: 'BUS', color: '#ef4444' },
      { region_id: 'R-003', name: '광주', code: 'GWJ', color: '#10b981' },
      { region_id: 'R-004', name: '대전', code: 'DJN', color: '#f59e0b' },
      { region_id: 'R-005', name: '대구', code: 'DGU', color: '#8b5cf6' }
    ]
  }
}

// 최신 인식 정보 목업 데이터
export const mockLatestRecognition = {
  data: {
    data: {
      waybill_id: 'WB-010',
      tracking_number: '012345678901',
      destination: '대구',
      confidence_score: 99.3,
      recognized_at: new Date().toISOString(),
      camera_id: 'CAM-01'
    }
  }
}

// 운송장 상세 목업 데이터
export const mockWaybillDetail = {
  data: {
    data: {
      waybill_id: 'WB-001',
      tracking_number: '123456789012',
      destination: '서울',
      status: 'COMPLETED',
      created_at: `${today}T09:15:32`,
      completed_at: `${today}T09:16:45`,
      process_time_sec: 73,
      confidence_score: 98.5,
      scan_logs: [
        { step: 'SCAN', timestamp: `${today}T09:15:32`, message: '운송장 스캔 시작' },
        { step: 'OCR', timestamp: `${today}T09:15:35`, message: 'OCR 인식 완료' },
        { step: 'CLASSIFY', timestamp: `${today}T09:15:40`, message: '분류 구역 결정: 서울' },
        { step: 'MOVE', timestamp: `${today}T09:15:45`, message: '컨베이어 이동 시작' },
        { step: 'COMPLETE', timestamp: `${today}T09:16:45`, message: '분류 완료' }
      ]
    }
  }
}
