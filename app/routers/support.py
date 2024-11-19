from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, Conversation
from ..services.dify.client import DifyClient
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/support", tags=["support"])

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    mode: Optional[str] = 'default'

@router.get("/bots")
async def get_available_bots():
    """利用可能なDifyボットの一覧を取得"""
    return [
        {
            "id": "default",
            "name": "一般サポート",
            "description": "一般的な質問に答えます"
        },
        {
            "id": "bot2",
            "name": "技術サポート",
            "description": "技術的な質問に答えます"
        },
        {
            "id": "bot3",
            "name": "その他",
            "description": "その他の質問に答えます"
        }
    ]

@router.post("/select/{bot_id}")
async def select_bot(bot_id: str):
    """特定のボットを選択"""
    return {"status": "success", "selected_bot_id": bot_id}

@router.post("/proxy/dify")
async def proxy_dify(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        # DifyClientのインスタンス化
        client = DifyClient(mode=request.mode)
        
        # Dify APIへのリクエスト
        response = await client.send_message(
            query=request.message,
            conversation_id=request.conversation_id
        )
        
        # レスポンスからDifyの会話IDを取得
        dify_conversation_id = response.get('conversation_id')
        
        if not request.conversation_id and dify_conversation_id:
            # 新規会話の場合、データベースに保存
            conversation = Conversation(
                user_id="test_user",  # 後で認証システムと連携
                title=request.message[:50],  # 最初のメッセージを会話タイトルとして使用
                dify_conversation_id=dify_conversation_id,
                mode=request.mode
            )
            db.add(conversation)
            db.commit()
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dify APIエラー: {str(e)}"
        ) 