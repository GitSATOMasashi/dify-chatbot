from typing import Optional
from pydantic import BaseModel

class DifyBot(BaseModel):
    id: str
    name: str
    description: str
    api_key: str

class DifyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def chat(self, message: str, conversation_id: Optional[str] = None):
        # Dify APIとの通信処理
        pass 