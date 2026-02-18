"""WebSocket routes."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """대시보드 실시간 업데이트 WebSocket."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, receive any messages from client
            data = await websocket.receive_text()
            # Echo back or process client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
