/**
 * 대시보드 데이터 관리 Composable
 */
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import {
  fetchDashboardStats,
  fetchWaybills,
  fetchDailyStats,
  fetchAlerts,
  getExportUrl,
  fetchOcrResults,
} from "../api";
import {
  STATUS_MAP,
  STATUS_PRIORITY,
  CITIES,
  CHART_COLORS,
  POLLING_INTERVALS,
  REGION_COLORS,
} from "../constants";
import { getToday } from "../utils/date";

export function useDashboard() {
  // 날짜 설정
  const maxDate = ref(getToday());
  const selectedDate = ref(getToday());

  // 목 데이터 (테스트용 - dev:mock 모드에서만 사용)
  const isMockMode = import.meta.env.MODE === "mock";
  const mockChartData = {
    completed: [
      { x: "전체", y: 45, fillColor: "#10b981" },
      { x: "서울", y: 18, fillColor: "#3b82f6" },
      { x: "부산", y: 12, fillColor: "#3b82f6" },
      { x: "광주", y: 8, fillColor: "#3b82f6" },
      { x: "대전", y: 4, fillColor: "#3b82f6" },
      { x: "대구", y: 3, fillColor: "#3b82f6" },
    ],
    pending: [
      { x: "전체", y: 22, fillColor: "#f59e0b" },
      { x: "서울", y: 7, fillColor: "#f59e0b" },
      { x: "부산", y: 5, fillColor: "#f59e0b" },
      { x: "광주", y: 4, fillColor: "#f59e0b" },
      { x: "대전", y: 3, fillColor: "#f59e0b" },
      { x: "대구", y: 3, fillColor: "#f59e0b" },
    ],
  };

  // 물류 목록 목 데이터
  const mockLogisticsData = [
    {
      id: "001",
      waybillId: 1,
      target: "서울",
      status: "완료",
      rawStatus: "COMPLETED",
      dateTime: "2026-02-05T13:45:00",
      processTime: 12,
      confidenceScore: 98.5,
    },
    {
      id: "002",
      waybillId: 2,
      target: "부산",
      status: "이동 중",
      rawStatus: "MOVING",
      dateTime: "2026-02-05T14:10:00",
      processTime: null,
      confidenceScore: 97.2,
    },
    {
      id: "003",
      waybillId: 3,
      target: "광주",
      status: "대기 중",
      rawStatus: "READY",
      dateTime: "2026-02-05T14:15:00",
      processTime: null,
      confidenceScore: 99.1,
    },
  ];

  // 반응형 데이터 (mock 모드일 때만 초기 데이터 설정)
  const chartSeries = ref(
    isMockMode
      ? [
          { name: "완료 건수", data: mockChartData.completed },
          { name: "남은 건수", data: mockChartData.pending },
        ]
      : [],
  );
  const logisticsData = ref(isMockMode ? mockLogisticsData : []);
  const latestScan = ref(null);
  const chartMax = ref(isMockMode ? 45 : 10);
  const isLoading = ref(false);
  const error = ref(null);

  // 추가 통계 데이터
  const dailyStats = ref(null);
  const alerts = ref([]);
  const successRateData = ref([]); // 날짜별 성공률 데이터 (최근 7일)
  const todaySummary = ref(
    isMockMode
      ? {
          total: 67,
          completed: 45,
          error: 0,
          avgProcessTime: 8,
          successRate: 67,
        }
      : {
          total: 0,
          completed: 0,
          error: 0,
          avgProcessTime: null,
          successRate: 0,
        },
  );

  // 필터
  const filterRegion = ref("전체");
  const filterStatus = ref("전체");

  // 폴링 인터벌 및 WebSocket
  let refreshInterval = null;
  let wsConnection = null;

  /**
   * 대시보드 데이터 로드
   */
  const loadData = async () => {
    isLoading.value = true;
    error.value = null;

    try {
      // 구역별 통계, 운송장 목록, 일별 통계, 알림, OCR 결과를 병렬로 호출
      // 날짜 필터링: 오늘 날짜인 경우 UTC 시차 문제로 데이터가 안 보일 수 있으므로
      // 날짜 필터를 제거하여 최근 데이터를 가져오도록 함
      const waybillParams = { size: 100 };
      // 선택한 날짜 기준으로 필터링 (모든 날짜에 동일하게 적용)
      if (selectedDate.value) {
        waybillParams.date = selectedDate.value;
      }

      const results = await Promise.allSettled([
        fetchDashboardStats(selectedDate.value),
        fetchWaybills(waybillParams),
        fetchAlerts({ resolved: false, size: 50 }),
        fetchOcrResults(50),
      ]);

      const statsRes =
        results[0].status === "fulfilled" ? results[0].value : { data: { data: [] } };
      const waybillsRes =
        results[1].status === "fulfilled" ? results[1].value : { data: { data: { items: [] } } };
      const alertsRes =
        results[2].status === "fulfilled" ? results[2].value : { data: { data: [] } };
      const ocrRes =
        results[3].status === "fulfilled" ? results[3].value : { data: { data: { items: [] } } };

      // Log errors if any
      results.forEach((res, index) => {
        if (res.status === "rejected") {
          console.error(`API call ${index} failed:`, res.reason);
        }
      });

      // 구역별 통계 처리
      const regionStats = statsRes.data.data || [];
      console.log("Region Stats Response:", regionStats); // 디버깅용 로그

      let totalDone = 0;
      let totalLeft = 0;
      let totalError = 0;
      let totalAll = 0;
      const finishedArr = [];
      const pendingArr = [];

      // 영문 지역명 매핑 (DB에 영문으로 저장된 경우 대응)
      const REGION_NAME_MAP = {
        Seoul: "서울",
        Busan: "부산",
        Gwangju: "광주",
        Daejeon: "대전",
        Daegu: "대구",
        seoul: "서울",
        busan: "부산",
        gwangju: "광주",
        daejeon: "대전",
        daegu: "대구",
      };

      CITIES.forEach((city, index) => {
        // 1. 정확히 일치하는 이름 찾기
        let cityData = regionStats.find((r) => r.region_name === city);

        // 2. 없으면 영문 매핑으로 찾기
        if (!cityData) {
          cityData = regionStats.find((r) => REGION_NAME_MAP[r.region_name] === city);
        }

        // 데이터가 없으면 0으로 초기화
        cityData = cityData || {
          completed: 0,
          ready: 0,
          moving: 0,
          error: 0,
        };

        const done = Number(cityData.completed || 0);
        const left = Number(cityData.ready || 0) + Number(cityData.moving || 0);
        const err = Number(cityData.error || 0);

        finishedArr.push({ x: city, y: done, fillColor: REGION_COLORS[index] });
        // pending: amber-500 (#f59e0b)
        pendingArr.push({ x: city, y: left + err, fillColor: "#f59e0b" });

        totalDone += done;
        totalLeft += left;
        totalError += err;
        totalAll += done + left + err;
      });

      // 전체 데이터 추가 (맨 앞)
      finishedArr.unshift({ x: "전체", y: totalDone, fillColor: CHART_COLORS.totalCompleted });
      pendingArr.unshift({ x: "전체", y: totalLeft + totalError, fillColor: "#f59e0b" });

      // Y축 최대값 계산
      const allValues = [...finishedArr.map((d) => d.y), ...pendingArr.map((d) => d.y)];
      const maxVal = Math.max(...allValues);
      chartMax.value = maxVal > 0 ? maxVal : 5;

      // 차트 시리즈 설정
      chartSeries.value = [
        { name: "완료 건수", data: finishedArr },
        { name: "남은 건수", data: pendingArr },
      ];

      // 운송장 목록 처리 (프론트엔드 날짜 필터링 강화)
      // 백엔드에서 이미 날짜 필터링 완료 → 프론트엔드 이중 필터링 제거
      const waybillItems = waybillsRes.data.data?.items || [];
      const waybillData = waybillItems.map((item) => ({
        id: item.tracking_number,
        waybillId: item.waybill_id,
        target: item.destination || "-",
        status: STATUS_MAP[item.status] || item.status,
        rawStatus: item.status,
        dateTime: item.completed_at || item.created_at || "",
        createdAt: item.created_at || "",
        completedAt: item.completed_at || null,
        processTime: item.process_time_sec || null,
        confidenceScore: item.confidence_score || null,
      }));

      // OCR 결과 처리 및 병합 (날짜 필터링 + 중복 제거)
      const ocrItems = ocrRes.data?.data?.items || [];
      const existingTrackingNumbers = new Set(waybillData.map((item) => item.id));

      const ocrData = ocrItems
        .filter((ocrItem) => {
          // 중복 제거
          if (existingTrackingNumbers.has(ocrItem.tracking_number)) return false;

          // 날짜 필터링 (선택된 날짜가 있는 경우)
          if (selectedDate.value) {
            const itemDate = (ocrItem.processed_at || "").split("T")[0];
            return itemDate === selectedDate.value;
          }
          return true;
        })
        .map((ocrItem) => ({
          id: ocrItem.tracking_number,
          waybillId: ocrItem.result_id || `OCR-${Date.now()}`,
          target: ocrItem.region_code || "-",
          status: "대기 중",
          rawStatus: "ready",
          dateTime: ocrItem.processed_at || new Date().toISOString(),
          createdAt: ocrItem.processed_at || new Date().toISOString(),
          completedAt: null,
          processTime: null,
          confidenceScore: null,
          recipientName: ocrItem.recipient_name,
          recipientAddress: ocrItem.recipient_address,
          senderName: ocrItem.sender_name,
          senderAddress: ocrItem.sender_address,
          isFromOcr: true,
        }));

      console.log("Waybill Data:", waybillData.length);
      console.log("OCR Data (Filtered):", ocrData.length);

      // waybill 데이터와 OCR 데이터 병합 -> 물류 목록에 표시될 최종 데이터
      logisticsData.value = [...ocrData, ...waybillData];

      // 오늘 요약 정보 업데이트
      // dailyStats가 있으면 그것을 우선 사용하고, 없으면 목록 데이터에서 계산
      const allItemsForSummary = [...ocrData, ...waybillData];
      const summaryTotal = allItemsForSummary.length;
      const summaryCompleted = allItemsForSummary.filter((i) => i.status === "완료").length;
      const summaryError = allItemsForSummary.filter((i) => i.status === "오류").length;

      // 평균 처리 시간 계산 (완료된 항목들의 processTime 평균)
      const completedItems = allItemsForSummary.filter(
        (i) => i.status === "완료" && i.processTime !== null,
      );
      let avgProcessTime = null;
      if (completedItems.length > 0) {
        const totalProcessTime = completedItems.reduce(
          (sum, item) => sum + (item.processTime || 0),
          0,
        );
        avgProcessTime = Math.round(totalProcessTime / completedItems.length);
      } else if (dailyStats.value?.avg_process_time_sec) {
        avgProcessTime = dailyStats.value.avg_process_time_sec;
      }

      // 선택된 날짜의 dailyStats가 있으면 해당 값 사용, 없으면 계산된 값 사용
      const selectedDayTotal = dailyStats.value?.total_count;
      const selectedDayCompleted = dailyStats.value?.completed_count;
      const selectedDayError = dailyStats.value?.error_count;

      todaySummary.value = {
        total: selectedDayTotal !== undefined ? selectedDayTotal : summaryTotal,
        completed: selectedDayCompleted !== undefined ? selectedDayCompleted : summaryCompleted,
        error: selectedDayError !== undefined ? selectedDayError : summaryError,
        avgProcessTime: avgProcessTime,
        successRate:
          dailyStats.value?.success_rate !== undefined
            ? Math.round(dailyStats.value.success_rate)
            : summaryTotal > 0
              ? Math.round((summaryCompleted / summaryTotal) * 100)
              : 0,
      };

      // 알림 데이터
      alerts.value = alertsRes.data.data?.items || alertsRes.data.data || [];

      // 최근 인식 정보 (OCR 또는 waybill 데이터 활용)
      const allItems = [...ocrData, ...waybillItems];
      if (allItems.length > 0) {
        const recentItem = ocrData.length > 0 ? ocrData[0] : waybillItems[0];
        if (ocrData.length > 0) {
          latestScan.value = {
            waybillId: recentItem.waybillId,
            destination: recentItem.target,
            matchRate: "-",
            camId: "CAM:OCR",
            waybill: recentItem.id,
            status: recentItem.rawStatus,
            processTime: null,
            scannedAt: recentItem.dateTime,
          };
        } else if (waybillItems.length > 0) {
          latestScan.value = {
            waybillId: waybillItems[0].waybill_id,
            destination: waybillItems[0].destination || "-",
            matchRate: waybillItems[0].confidence_score
              ? `${waybillItems[0].confidence_score.toFixed(1)}%`
              : "-",
            camId: "CAM:01",
            waybill: waybillItems[0].tracking_number,
            status: waybillItems[0].status,
            processTime: waybillItems[0].process_time_sec,
            scannedAt: waybillItems[0].created_at,
          };
        }
      } else {
        latestScan.value = null;
      }
    } catch (err) {
      console.error("데이터 로드 실패:", err);
      error.value = err.message || "데이터를 불러오는데 실패했습니다.";
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * 엑셀 다운로드
   */
  /**
   * 엑셀 다운로드 (옵션: date 또는 { startDate, endDate })
   * 인자가 없으면 전체 다운로드
   */
  const downloadExcel = (options) => {
    // options가 있으면 그대로 사용, 없으면 전체 (또는 현재 선택된 날짜 로직 제거)
    // HomeView에서 명시적으로 호출하도록 변경
    const url = getExportUrl(options);
    window.open(url, "_blank");
  };

  /**
   * 필터링된 물류 데이터 (computed)
   */
  const filteredLogisticsData = computed(() => {
    const filtered = logisticsData.value.filter((item) => {
      const regionMatch = filterRegion.value === "전체" || item.target === filterRegion.value;
      const statusMatch = filterStatus.value === "전체" || item.status === filterStatus.value;
      return regionMatch && statusMatch;
    });

    return filtered.sort((a, b) => {
      const priorityA = STATUS_PRIORITY[a.status] || 99;
      const priorityB = STATUS_PRIORITY[b.status] || 99;

      if (priorityA !== priorityB) return priorityA - priorityB;
      if (a.dateTime < b.dateTime) return 1;
      if (a.dateTime > b.dateTime) return -1;
      return 0;
    });
  });

  /**
   * 로컬 물류 데이터에서 차트 즉시 재계산 (WebSocket 이벤트 후 호출)
   */
  const updateChartFromLocal = () => {
    let totalDone = 0;
    let totalLeft = 0;
    const finishedArr = [];
    const pendingArr = [];

    CITIES.forEach((city, index) => {
      const cityItems = logisticsData.value.filter((item) => item.target === city);
      const done = cityItems.filter((item) => item.rawStatus === "COMPLETED").length;
      const left = cityItems.filter((item) => item.rawStatus !== "COMPLETED").length;

      finishedArr.push({ x: city, y: done, fillColor: REGION_COLORS[index] });
      pendingArr.push({ x: city, y: left, fillColor: "#f59e0b" });

      totalDone += done;
      totalLeft += left;
    });

    finishedArr.unshift({ x: "전체", y: totalDone, fillColor: CHART_COLORS.totalCompleted });
    pendingArr.unshift({ x: "전체", y: totalLeft, fillColor: "#f59e0b" });

    const allValues = [...finishedArr.map((d) => d.y), ...pendingArr.map((d) => d.y)];
    const maxVal = Math.max(...allValues);
    chartMax.value = maxVal > 0 ? maxVal : 5;

    chartSeries.value = [
      { name: "완료 건수", data: finishedArr },
      { name: "남은 건수", data: pendingArr },
    ];
  };

  /**
   * 폴링 시작
   */
  const startPolling = () => {
    stopPolling();
    refreshInterval = setInterval(loadData, POLLING_INTERVALS.dashboard);
  };

  /**
   * 폴링 중지
   */
  const stopPolling = () => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  };

  /**
   * OCR 결과를 물류 테이블에 추가 (WebSocket으로 받은 실시간 데이터)
   */
  const addOcrResultToLogistics = (payload) => {
    // status check: allow 'completed' (from OCR) or 'ready' (from Waybill update)
    if (!payload || (payload.status !== "completed" && payload.status !== "ready")) return;

    // 중복 체크
    const exists = logisticsData.value.some((item) => item.id === payload.tracking_number);
    if (exists) return;

    const newItem = {
      id: payload.tracking_number,
      waybillId: payload.result_id || `OCR-${Date.now()}`,
      target: payload.region_code || "-",
      status: "대기 중",
      rawStatus: "ready",
      dateTime: payload.processed_at || new Date().toISOString(),
      processTime: null,
      confidenceScore: null,
      // OCR 추가 정보
      recipientName: payload.recipient_name || null,
      recipientAddress: payload.recipient_address || null,
      senderName: payload.sender_name || null,
      senderAddress: payload.sender_address || null,
      isFromOcr: true, // OCR에서 온 데이터임을 표시
    };

    // 맨 앞에 추가
    logisticsData.value.unshift(newItem);

    // 최신 스캔 정보 업데이트
    latestScan.value = {
      waybillId: newItem.waybillId,
      destination: newItem.target,
      matchRate: "-",
      camId: "CAM:OCR",
      waybill: newItem.id,
      status: newItem.rawStatus,
      processTime: null,
      scannedAt: newItem.dateTime,
    };

    // 오늘 요약 업데이트
    todaySummary.value.total += 1;
  };

  /**
   * WebSocket 연결 설정
   */
  const setupWebSocket = () => {
    try {
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/dashboard`;

      wsConnection = new WebSocket(wsUrl);

      wsConnection.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === "ocr_result") {
            // OCR 결과를 물류 테이블에 자동 추가
            addOcrResultToLogistics(message.payload);
            updateChartFromLocal();
          } else if (message.type === "waybill_update") {
            // 물류 상태 업데이트
            const data = message.data;

            if (data.status === "completed") {
              // 완료 상태 업데이트: 기존 아이템을 찾아서 상태 변경
              const existing = logisticsData.value.find((item) => item.id === data.tracking_number);
              if (existing) {
                existing.status = STATUS_MAP["COMPLETED"] || "완료";
                existing.rawStatus = "COMPLETED";
                existing.completedAt = new Date().toISOString();
              }
            } else {
              // 새 아이템 추가 (OCR 인식 직후)
              const mappedPayload = {
                tracking_number: data.tracking_number,
                result_id: String(data.waybill_id),
                region_code: data.destination,
                status: "ready",
                processed_at: new Date().toISOString(),
              };
              addOcrResultToLogistics(mappedPayload);
            }
            // 로컬 데이터 기반 차트 즉시 갱신
            updateChartFromLocal();
          }
        } catch (e) {
          console.debug("WebSocket message parse error:", e);
        }
      };

      wsConnection.onclose = () => {
        console.debug("WebSocket closed, attempting reconnect in 5s");
        setTimeout(setupWebSocket, 5000);
      };

      wsConnection.onerror = (error) => {
        console.debug("WebSocket error:", error);
      };
    } catch (error) {
      console.debug("WebSocket connection failed:", error);
    }
  };

  /**
   * WebSocket 연결 종료
   */
  const closeWebSocket = () => {
    if (wsConnection) {
      wsConnection.close();
      wsConnection = null;
    }
  };

  // 날짜 변경 감시
  watch(selectedDate, () => {
    loadData();
  });

  // 컴포넌트 마운트 시 초기화
  onMounted(() => {
    loadData();
    startPolling();
    setupWebSocket(); // WebSocket 연결 시작
  });

  // 컴포넌트 언마운트 시 정리
  onUnmounted(() => {
    stopPolling();
    closeWebSocket(); // WebSocket 연결 종료
  });

  return {
    // 상태
    maxDate,
    selectedDate,
    chartSeries,
    chartMax,
    logisticsData,
    filteredLogisticsData,
    latestScan,
    isLoading,
    error,

    // 추가 통계
    dailyStats,
    alerts,
    todaySummary,
    successRateData,

    // 필터
    filterRegion,
    filterStatus,

    // 메서드
    loadData,
    startPolling,
    stopPolling,
    downloadExcel,
  };
}
