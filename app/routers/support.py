from fastapi import APIRouter, Depends
from ..services.dify.client import DifyClient, DifyBot

router = APIRouter(prefix="/support", tags=["support"])

@router.get("/bots")
async def get_available_bots():
    """利用可能なDifyボットの一覧を取得"""
    return [
        {
            "id": "bot1",
            "name": "一般サポート",
            "description": "一般的な質問に答えます"
        }
    ]

@router.post("/select/{bot_id}")
async def select_bot(bot_id: str):
    """特定のボットを選択"""
    return {"status": "success", "selected_bot_id": bot_id} 