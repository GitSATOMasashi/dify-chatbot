from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect, HTTPException  # HTTPExceptionを追加
from typing import Dict
import httpx  # aiohttpの代わりにhttpxを使用
import json
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware  # 追加

load_dotenv()
router = APIRouter()

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.api_key = os.getenv("DIFY_API_KEY")  # 環境変数からAPIキーを取得
        
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
    async def send_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def _call_dify_api(self, message: str, user_id: str) -> dict:  # クラス内のメソッドとして定義
        """Dify APIとの実際の通信処理"""
        url = "https://api.dify.ai/v1/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": {},
            "query": message,
            "user": user_id,
            "response_mode": "blocking",
            "conversation_id": None  # 必要に応じて会話IDを管理
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Dify API error: {response.text}"
                )

    async def send_to_dify(self, message: str, user_id: str) -> dict:
        try:
            response = await self._call_dify_api(message, user_id)
            return {
                "type": "bot",
                "content": response.get("answer", "応答がありません"),
                "conversation_id": response.get("conversation_id")
            }
        except Exception as e:
            return {
                "type": "error",
                "content": f"エラーが発生しました: {str(e)}"
            }

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # メッセージを処理してDify APIに送信
            response = await manager.send_to_dify(
                message=data.get("message", ""),
                user_id=user_id
            )
            
            # 応答をクライアントに送信
            await manager.send_message(response, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        await manager.send_message(
            {
                "type": "error",
                "content": f"エラーが発生しました: {str(e)}"
            },
            user_id
        )
