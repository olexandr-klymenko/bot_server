from typing import List

from fastapi import WebSocketDisconnect, WebSocket, APIRouter


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, client_type, client_id):
        await websocket.accept()
        print(f"client type: {client_type}")
        print(f"name: {client_id}")
        session_info = {
            "board": "######",
            "players": {"score": {}, "names": []},
            "size": 16,
        }
        await websocket.send_json(session_info)
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/")
async def editor_web_socket(websocket: WebSocket, client_type, client_id):
    await manager.connect(websocket, client_type, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
