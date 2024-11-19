from typing import Optional, Dict, Any
from pydantic import BaseModel
from ...config import DIFY_API_KEYS
import httpx
from fastapi import HTTPException

class DifyBot(BaseModel):
    id: str
    name: str
    description: str
    api_key: str

class DifyClient:
    def __init__(self, mode: str = 'default'):
        self.api_key = self._get_api_key(mode)
        self.base_url = "https://api.dify.ai/v1"
    
    async def send_message(
        self, 
        query: str, 
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat-messages",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "inputs": {},
                        "query": query,
                        "response_mode": "blocking",
                        "conversation_id": conversation_id or "",
                        "user": "test_user"
                    },
                    timeout=30.0  # タイムアウトを30秒に設定
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Dify API error: {response.text}"
                    )
                    
                return response.json()
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Dify APIがタイムアウトしました"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Dify APIリクエストエラー: {str(e)}"
            )