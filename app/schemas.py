from pydantic import BaseModel

class MessageCreate(BaseModel):
    content: str
    role: str
    conversation_id: str
    user_id: str = "test_user" 