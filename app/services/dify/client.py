from typing import Optional
from pydantic import BaseModel
from ...config import DIFY_API_KEYS
import httpx

class DifyBot(BaseModel):
    id: str
    name: str
    description: str
    api_key: str

class DifyClient:
    def __init__(self, mode: str = 'default'):
        self.api_key = DIFY_API_KEYS.get(mode, DIFY_API_KEYS['default'])
        self.base_url = "https://api.dify.ai/v1"
        
    async def send_message(
        self, 
        query: str, 
        conversation_id: Optional[str] = None
    ):
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
                }
            )
            return response.json()