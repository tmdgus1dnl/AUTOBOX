
import os
import re
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.waybill import LogisticsItem

# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "./data"

def parse_file_timestamp(filename):
    # Format: box_img_YYYYMMDD_HHMMSS_micros.json
    match = re.search(r'box_img_(\d{8})_(\d{6})', filename)
    if match:
        dt_str = f"{match.group(1)}{match.group(2)}"
        return datetime.strptime(dt_str, "%Y%m%d%H%M%S")
    return None

def backfill():
    db = SessionLocal()
    try:
        # Get all items without image
        items = db.query(LogisticsItem).filter(LogisticsItem.image_file == None).all()
        logger.info(f"Found {len(items)} items to backfill")

        # Get all box_img files
        files = []
        for f in os.listdir(DATA_DIR):
            if f.startswith("box_img_") and f.endswith(".json"):
                dt = parse_file_timestamp(f)
                if dt:
                    files.append({"name": f, "time": dt})
        
        logger.info(f"Found {len(files)} image files")

        updated_count = 0
        for item in items:
            # Determine item time in KST
            # If created before 2026-02-08 (today), assume it was stored as UTC -> convert to KST
            # The cutoff is arbitrary but effective for this specific case
            item_time = item.created_at
            
            # Heuristic: if hour < 9 and date is before today, it's likely UTC
            # But simpler: check if adding 9 hours matches a file
            
            # Strategy: find closest file within 60 seconds
            # Try both raw time and raw+9h time
            
            candidates = []
            
            # 1. As-is (if already KST)
            candidates.append(item_time)
            
            # 2. As UTC (+9h to get KST)
            candidates.append(item_time + timedelta(hours=9))
            
            best_file = None
            min_diff = timedelta(seconds=60)
            
            for target_time in candidates:
                for f in files:
                    file_time = f["time"]
                    # File should be created BEFORE DB record (or very slightly after due to clock skew, but usually before)
                    # OCR process: Create File -> Call API -> Save to DB. So File is older.
                    # Diff = DB - File. Should be positive.
                    diff = target_time - file_time
                    
                    if timedelta(seconds=0) <= diff < min_diff:
                        min_diff = diff
                        best_file = f["name"]
            
            if best_file:
                item.image_file = best_file
                updated_count += 1
                logger.info(f"Matched {item.tracking_number} to {best_file} (diff: {min_diff})")
            else:
                logger.warning(f"No match for {item.tracking_number} (Created: {item.created_at})")
        
        db.commit()
        logger.info(f"Backfill complete. Updated {updated_count} items.")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
