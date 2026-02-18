"""
물류 테스트 데이터 생성 스크립트
2월 4일부터 과거 5일동안 (1월 31일 ~ 2월 4일) 각 날짜당 20개씩 임의 데이터 생성
지역: 광주, 부산, 대구, 서울, 대전
"""

import random
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 환경변수에서 DATABASE_URL 읽기
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    from app.config import get_settings
    database_url = get_settings().DATABASE_URL

# Azure MySQL SSL 연결 설정
engine = create_engine(
    database_url,
    connect_args={"ssl": {"ssl_disabled": False}}
)

# 지역 목록
DESTINATIONS = ["광주", "부산", "대구", "서울", "대전"]

# 상태 목록 (COMPLETED 위주로 설정)
STATUSES = ["COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED", "ERROR"]

def generate_tracking_number():
    """8자리 랜덤 운송장 번호 생성"""
    return str(random.randint(10000000, 99999999))

def generate_test_data():
    """테스트 데이터 생성 및 삽입"""
    
    # 2026년 2월 4일 기준 과거 5일
    base_date = datetime(2026, 2, 4)
    
    data_to_insert = []
    
    for day_offset in range(5):  # 0~4일 전 (2/4, 2/3, 2/2, 2/1, 1/31)
        target_date = base_date - timedelta(days=day_offset)
        
        for i in range(20):  # 각 날짜당 20개
            tracking_number = generate_tracking_number()
            destination = random.choice(DESTINATIONS)
            status = random.choice(STATUSES)
            
            # 랜덤 시간 (04:00 ~ 20:00 사이)
            hour = random.randint(4, 20)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            created_at = target_date.replace(hour=hour, minute=minute, second=second)
            
            # 완료 시간 (생성 후 1~10분 사이)
            if status == "COMPLETED":
                process_time = random.randint(60, 600)  # 1분 ~ 10분
                completed_at = created_at + timedelta(seconds=process_time)
            else:
                completed_at = None
            
            # 최종 수정 시간
            updated_at = datetime(2026, 2, 6, 1, 2, 43)  # 현재 시간으로 고정
            
            data_to_insert.append({
                "tracking_number": tracking_number,
                "destination": destination,
                "status": status,
                "created_at": created_at,
                "completed_at": completed_at,
                "updated_at": updated_at
            })
    
    return data_to_insert

def insert_data(data):
    """데이터베이스에 데이터 삽입"""
    
    with engine.connect() as conn:
        for item in data:
            # logistics_item 삽입
            logistics_sql = text("""
                INSERT INTO logistics_item 
                (tracking_number, destination, status, created_at, completed_at, updated_at)
                VALUES (:tracking_number, :destination, :status, :created_at, :completed_at, :updated_at)
            """)
            
            conn.execute(logistics_sql, item)
            
            # waybill_map 삽입 (자동 ID 생성)
            waybill_sql = text("""
                INSERT INTO waybill_map (tracking_number)
                VALUES (:tracking_number)
            """)
            
            conn.execute(waybill_sql, {"tracking_number": item["tracking_number"]})
        
        conn.commit()
    
    print(f"총 {len(data)}개의 테스트 데이터가 입력되었습니다.")

def main():
    print("테스트 데이터 생성 중...")
    data = generate_test_data()
    
    print(f"\n생성된 데이터 요약:")
    
    # 날짜별 통계
    from collections import defaultdict
    date_stats = defaultdict(lambda: {"count": 0, "regions": defaultdict(int)})
    
    for item in data:
        date_key = item["created_at"].strftime("%Y-%m-%d")
        date_stats[date_key]["count"] += 1
        date_stats[date_key]["regions"][item["destination"]] += 1
    
    for date_key in sorted(date_stats.keys()):
        stats = date_stats[date_key]
        regions = ", ".join([f"{k}:{v}" for k, v in stats["regions"].items()])
        print(f"  {date_key}: {stats['count']}개 ({regions})")
    
    print("\n데이터베이스에 입력 중...")
    insert_data(data)
    print("완료!")

if __name__ == "__main__":
    main()
