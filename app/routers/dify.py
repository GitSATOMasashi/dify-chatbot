from fastapi import APIRouter, Depends
from typing import List

router = APIRouter(prefix="/dify", tags=["dify"])

@router.get("/bots")
async def get_available_bots() -> List[dict]:
    """利用可能なDifyボットの一覧を取得"""
    return [
        {
            "id": "support_1",
            "name": "一般サポート",
            "description": "一般的な質問に答えます",
            "api_key": "..."  # 環境変数から取得
        },
        {
            "id": "support_2",
            "name": "技術サポート",
            "description": "技術的な質問に答えます",
            "api_key": "..."  # 環境変数から取得
        }
    ]

@router.post("/select/{bot_id}")
async def select_bot(bot_id: str):
    """特定のボットを選択"""
    return {"status": "success", "selected_bot_id": bot_id}
