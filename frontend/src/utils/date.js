/**
 * 날짜 관련 유틸리티 함수
 */

/**
 * 오늘 날짜를 YYYY-MM-DD 형식으로 반환
 * @returns {string} 오늘 날짜 문자열
 */
export const getToday = () => {
  const now = new Date()
  const offset = now.getTimezoneOffset() * 60000
  const today = new Date(now - offset)
  return today.toISOString().split('T')[0]
}

/**
 * 날짜 문자열에서 시간만 추출
 * @param {string} dateTimeStr - 날짜시간 문자열 (예: "2024-01-15 14:30:00")
 * @returns {string} 시간 문자열 (예: "14:30:00")
 */
export const extractTime = (dateTimeStr) => {
  if (!dateTimeStr) return ''
  const parts = dateTimeStr.split(' ')
  return parts.length > 1 ? parts[1] : ''
}

/**
 * 날짜 포맷팅
 * @param {string|Date} date - 날짜
 * @param {string} format - 포맷 (기본값: 'YYYY-MM-DD')
 * @returns {string} 포맷된 날짜 문자열
 */
export const formatDate = (date, format = 'YYYY-MM-DD') => {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}
