"""OCR Service for automatic image processing.

Watches the data directory for new box_img JSON files,
calls the external OCR API, and broadcasts results via WebSocket.
"""

import asyncio
import json
import logging
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
# Use PollingObserver for reliable detection in Docker volumes
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from app.config import get_settings
from app.services.websocket import manager as ws_manager
from app.database import SessionLocal
from app.models.waybill import LogisticsItem, LogisticsStatus, WaybillMap

logger = logging.getLogger(__name__)
settings = get_settings()

# Region code mapping: 파싱해서 그래프에 보이는 도시명으로 변환
REGION_MAP = {
    '서울': '서울',
    '부산': '부산',
    '광주': '광주',
    '대전': '대전',
    '대구': '대구',
    'CH': '광주',  # CH로 시작하면 광주로 매핑 (예시)
}

# MQTT Signal Mapping
REGION_SIGNAL_MAP = {
    '서울': 'E',
    '대구': 'F',
    '대전': 'D',
    '광주': 'C',
    '부산': 'B'
}
DEFAULT_SIGNAL = 'A'

def parse_region_code(region_code: Optional[str]) -> str:
    # ... existing implementation ...
    if not region_code:
        return '-'
    
    # 숫자 제거해서 지역명만 추출
    region_name = re.sub(r'[0-9]+', '', region_code).strip()
    
    # 알려진 지역매핑에서 찾기
    for key, value in REGION_MAP.items():
        if region_name.upper().startswith(key.upper()):
            return value
    
    # 매핑에 없으면 None 반환 (유효하지 않은 지역)
    return None


# 알려진 지역 키워드 목록
KNOWN_REGIONS = ['서울', '부산', '광주', '대전', '대구']

def _extract_region_from_all_values(values: list) -> Optional[str]:
    """모든 OCR 결과 값에서 알려진 지역명을 찾아 반환.
    
    VLM 모델이 값 순서를 바꾸거나 잘못 매핑해도
    어떤 필드에서든 지역명이 발견되면 사용합니다.
    """
    for val in values:
        if not val:
            continue
        text = str(val)
        for region in KNOWN_REGIONS:
            if region in text:
                return region
    return None




class OCRResult:
    """OCR processing result data."""
    
    def __init__(
        self,
        result_id: str,
        source_file: str,
        tracking_number: Optional[str] = None,
        region_code: Optional[str] = None,
        recipient_name: Optional[str] = None,
        recipient_address: Optional[str] = None,
        sender_name: Optional[str] = None,
        sender_address: Optional[str] = None,
        raw_response: Optional[Dict] = None,
        status: str = "pending",
        error: Optional[str] = None,
        processed_at: Optional[str] = None
    ):
        self.result_id = result_id
        self.source_file = source_file
        self.tracking_number = tracking_number
        self.region_code = region_code
        self.recipient_name = recipient_name
        self.recipient_address = recipient_address
        self.sender_name = sender_name
        self.sender_address = sender_address
        self.raw_response = raw_response
        self.status = status
        self.error = error
        self.processed_at = processed_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "source_file": self.source_file,
            "tracking_number": self.tracking_number,
            "region_code": self.region_code,
            "recipient_name": self.recipient_name,
            "recipient_address": self.recipient_address,
            "sender_name": self.sender_name,
            "sender_address": self.sender_address,
            "raw_response": self.raw_response,
            "status": self.status,
            "error": self.error,
            "processed_at": self.processed_at
        }


class BoxImageHandler(FileSystemEventHandler):
    """File system event handler for box_img JSON files."""
    
    def __init__(self, ocr_service: 'OCRService'):
        super().__init__()
        self.ocr_service = ocr_service
        self._processed_files = set()
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_name = os.path.basename(file_path)
        
        # Only process box_img JSON files
        if not file_name.startswith("box_img_") or not file_name.endswith(".json"):
            return
        
        # Avoid processing the same file multiple times
        if file_path in self._processed_files:
            return
        
        self._processed_files.add(file_path)
        
        logger.info(f"New box image file detected: {file_name}")
        
        # Wait a bit for file to be fully written
        time.sleep(0.5)
        
        # Process in a separate thread
        threading.Thread(
            target=self.ocr_service.process_file,
            args=(file_path,),
            daemon=True
        ).start()


class OCRService:
    """OCR Service for automatic image processing."""
    
    def __init__(self):
        # Use settings from config.py - easily configurable via .env file
        self.watch_directory = settings.OCR_WATCH_DIR
        self.api_url = settings.OCR_API_URL
        self.enabled = settings.OCR_ENABLED
        self._observer: Optional[Observer] = None
        self._results: List[OCRResult] = []
        self._max_results = 100
        self._http_client: Optional[httpx.AsyncClient] = None
    
    def start(self):
        """Start the file watcher."""
        if not self.enabled:
            logger.info("OCR Service is disabled")
            return
        
        # Ensure watch directory exists
        Path(self.watch_directory).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting OCR Service - watching: {self.watch_directory}")
        logger.info(f"OCR API URL: {self.api_url}")
        
        # Create and start the observer
        self._observer = Observer()
        handler = BoxImageHandler(self)
        self._observer.schedule(handler, self.watch_directory, recursive=False)
        self._observer.start()
        
        # Load recent results from DB to restore memory state
        self._load_recent_results_from_db()
        
        logger.info("OCR Service started successfully")

    def _load_recent_results_from_db(self):
        """Load recent OCR results from database to repopulate memory."""
        try:
            db = SessionLocal()
            # Fetch recent items with WaybillMap to get numeric ID
            recent_items = db.query(LogisticsItem, WaybillMap)\
                .join(WaybillMap, LogisticsItem.tracking_number == WaybillMap.tracking_number)\
                .order_by(LogisticsItem.created_at.desc())\
                .limit(20)\
                .all()
            
            for item, mapping in recent_items:
                # Reconstruct OCRResult objects
                result = OCRResult(
                    result_id=str(mapping.waybill_id), # Use numeric ID
                    source_file="From DB",
                    tracking_number=item.tracking_number,
                    region_code=item.destination,
                    status="completed",
                    processed_at=item.created_at.isoformat() if item.created_at else None
                )
                self._add_result(result)
            
            logger.info(f"Loaded {len(recent_items)} recent results from DB")
            db.close()
        except Exception as e:
            logger.error(f"Failed to load info from DB: {e}")
    
    def stop(self):
        """Stop the file watcher."""
        if self._observer:
            logger.info("Stopping OCR Service...")
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            logger.info("OCR Service stopped")
    
    def process_file(self, file_path: str):
        """Process a box image JSON file."""
        file_name = os.path.basename(file_path)
        result_id = f"OCR-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        result = OCRResult(
            result_id=result_id,
            source_file=file_name,
            status="processing"
        )
        
        try:
            logger.info(f"Processing file: {file_name}")
            
            # Read the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract base64 image data
            image_base64 = data.get("dest")
            
            if not image_base64:
                raise ValueError("No 'dest' field containing image data found")
            
            logger.info(f"Image data length: {len(image_base64)} characters")
            
            # Call OCR API
            ocr_response = self._call_ocr_api_sync(image_base64)
            
            if ocr_response:
                result.raw_response = ocr_response
                
                # Check if OCR was successful
                if ocr_response.get("success") == True:
                    result.status = "completed"
                    
                    # Parse the result field which contains a JSON string
                    # Response format: {"result": "{JSON string}", "success": true, "message": "..."}
                    result_str = ocr_response.get("result", "")
                    
                    if result_str:
                        try:
                            # Parse the JSON string inside result
                            result_data = json.loads(result_str)
                            
                            # Extract values by ORDER (key names may vary from VLM model)
                            # Expected order: tracking_number, region_code, recipient_name, 
                            #                 recipient_address, sender_name, sender_address
                            values = list(result_data.values())
                            
                            if len(values) >= 1:
                                result.tracking_number = str(values[0]) if values[0] else None
                            if len(values) >= 2:
                                # 1차: 위치 기반 파싱 (values[1])
                                raw_region = str(values[1]) if values[1] else None
                                parsed = parse_region_code(raw_region)
                                
                                if parsed:
                                    result.region_code = parsed
                                else:
                                    # 2차: 모든 값에서 지역명 검색 (VLM 순서 오류 대비)
                                    fallback = _extract_region_from_all_values(values)
                                    result.region_code = fallback if fallback else '-'
                                    if fallback:
                                        logger.info(f"Region found via fallback scan: {fallback} (original value[1]: {raw_region})")
                            if len(values) >= 3:
                                result.recipient_name = str(values[2]) if values[2] else None
                            if len(values) >= 4:
                                result.recipient_address = str(values[3]) if values[3] else None
                            if len(values) >= 5:
                                result.sender_name = str(values[4]) if values[4] else None
                            if len(values) >= 6:
                                result.sender_address = str(values[5]) if values[5] else None
                            
                            logger.info(f"OCR completed for {file_name}: tracking={result.tracking_number}, region={result.region_code}")
                            
                            # Save to Database
                            db_id = self._save_to_database(result, source_file=file_name)
                            if db_id:
                                result.result_id = str(db_id)  # Use simpler DB ID
                                logger.info(f"Saved to DB with ID: {db_id}")
                                
                                # 1분 후 자동 완료 타이머 시작
                                self._schedule_auto_complete(
                                    result.tracking_number, db_id, delay_seconds=60
                                )

                            # Auto-dispatch MQTT signal if region code is available
                            try:
                                from app.services.mqtt import mqtt_service
                                
                                # Determine signal
                                signal = REGION_SIGNAL_MAP.get(result.region_code)
                                
                                if signal:
                                    # Payload format: {"destination": "B"}
                                    payload = json.dumps({"destination": signal})
                                    
                                    # Topic: server_msg/dest (mqtt_service automatically adds prefix 'server_msg/')
                                    mqtt_service.publish("command/dest", payload, qos=1)
                                    
                                    logger.info(f"Auto-dispatched MQTT signal '{signal}' to topic 'server_msg/dest'")
                                else:
                                    logger.info(f"No signal mapped for region '{result.region_code}', skipping MQTT dispatch")
                                
                            except Exception as mqtt_err:
                                logger.error(f"Failed to auto-dispatch MQTT signal: {mqtt_err}")
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse result JSON: {e}, using raw result")
                            result.tracking_number = result_str
                else:
                    result.status = "error"
                    result.error = ocr_response.get("message", "OCR processing failed")
            else:
                result.status = "error"
                result.error = "No response from OCR API"
                
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")
            result.status = "error"
            result.error = str(e)
        
        # Store result
        self._add_result(result)
        
        # Broadcast to WebSocket clients
        self._broadcast_result(result)
        
        return result
    
    def _save_to_database(self, result: OCRResult, source_file: str = None) -> Optional[int]:
        """Save OCR result to database and return the new waybill_id."""
        if not result.tracking_number:
            return None
            
        db = SessionLocal()
        try:
            # Check if exists
            existing = db.query(LogisticsItem).filter(LogisticsItem.tracking_number == result.tracking_number).first()
            
            if not existing:
                # Create LogisticsItem
                item = LogisticsItem(
                    tracking_number=result.tracking_number,
                    destination=result.region_code,
                    image_file=source_file,
                    status=LogisticsStatus.READY,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(item)
                db.flush()  # To satisfy foreign key constraints
                
                # Create WaybillMap to get simple ID
                mapping = WaybillMap(tracking_number=result.tracking_number)
                db.add(mapping)
                db.commit()
                db.refresh(mapping)
                
                return mapping.waybill_id
            else:
                # If exists, we might want to return the existing waybill_id
                mapping = db.query(WaybillMap).filter(WaybillMap.tracking_number == result.tracking_number).first()
                if mapping:
                    return mapping.waybill_id
                    
        except Exception as e:
            logger.error(f"Database save error: {e}")
            db.rollback()
        finally:
            db.close()
            
        return None
    
    def _schedule_auto_complete(self, tracking_number: str, waybill_id: int, delay_seconds: int = 60):
        """1분 후 자동으로 COMPLETED 처리하는 백그라운드 타이머."""
        import threading
        
        def _auto_complete():
            import time
            time.sleep(delay_seconds)
            
            db = SessionLocal()
            try:
                item = db.query(LogisticsItem).filter(
                    LogisticsItem.tracking_number == tracking_number
                ).first()
                
                if item and item.status != LogisticsStatus.COMPLETED:
                    now = datetime.now()
                    item.status = LogisticsStatus.COMPLETED
                    item.completed_at = now
                    item.updated_at = now
                    db.commit()
                    
                    logger.info(f"Auto-completed after {delay_seconds}s: {tracking_number}")
                    
                    # WebSocket broadcast
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            ws_manager.broadcast({
                                "type": "waybill_update",
                                "data": {
                                    "waybill_id": waybill_id,
                                    "tracking_number": tracking_number,
                                    "status": "completed",
                                    "destination": item.destination
                                }
                            })
                        )
                        loop.close()
                    except Exception as e:
                        logger.debug(f"Could not broadcast auto-complete: {e}")
                else:
                    logger.debug(f"Skip auto-complete for {tracking_number}: already completed or not found")
            except Exception as e:
                logger.error(f"Auto-complete error for {tracking_number}: {e}")
            finally:
                db.close()
        
        t = threading.Thread(target=_auto_complete, daemon=True)
        t.start()
        logger.info(f"Scheduled auto-complete for {tracking_number} in {delay_seconds}s")
    
    def _call_ocr_api_sync(self, image_base64: str) -> Optional[Dict]:
        """Call OCR API synchronously."""
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self.api_url,
                    json={"image_base64": image_base64},
                    headers={
                        "Content-Type": "application/json",
                        "ngrok-skip-browser-warning": "true"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"OCR API returned status {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling OCR API: {e}")
            return None
    
    def _add_result(self, result: OCRResult):
        """Add a result to the history."""
        self._results.insert(0, result)
        
        # Keep only the most recent results
        if len(self._results) > self._max_results:
            self._results = self._results[:self._max_results]
    
    def _broadcast_result(self, result: OCRResult):
        """Broadcast OCR result to WebSocket clients."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 1. OCR Result Broadcast
            loop.run_until_complete(
                ws_manager.broadcast({
                    "type": "ocr_result",
                    "payload": result.to_dict()
                })
            )
            
            # 2. Waybill Update Broadcast (for logistics list consistency)
            # Send this if we have a valid numeric ID (meaning saved to DB)
            if result.tracking_number and result.result_id and result.result_id.isdigit():
                 loop.run_until_complete(
                    ws_manager.broadcast({
                        "type": "waybill_update",
                        "data": {
                            "waybill_id": int(result.result_id),
                            "tracking_number": result.tracking_number,
                            "status": "ready", # Initial status in DB is READY
                            "destination": result.region_code
                        }
                    })
                 )

            loop.close()
        except Exception as e:
            logger.debug(f"Could not broadcast OCR result: {e}")
    
    def get_results(self, limit: int = 20) -> List[Dict]:
        """Get recent OCR results."""
        return [r.to_dict() for r in self._results[:limit]]
    
    def get_result(self, result_id: str) -> Optional[Dict]:
        """Get a specific OCR result by ID."""
        for result in self._results:
            if result.result_id == result_id:
                return result.to_dict()
        return None


# Global OCR service instance
ocr_service = OCRService()
