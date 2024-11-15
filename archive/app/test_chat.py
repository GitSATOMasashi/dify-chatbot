from config import DIFY_API_KEY
from token_manager import TokenManager
import requests

def chat_with_token_limit(user_id: str, message: str):
    token_manager = TokenManager(daily_limit=1000)
    url = 'https://api.dify.ai/v1/chat-messages'
    headers = {
        'Authorization': f'Bearer {DIFY_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 予測トークン数（簡易的な計算）
        estimated_tokens = len(message) // 4
        
        # トークン使用量をチェック
        current_usage = token_manager.get_daily_usage(user_id)
        if current_usage + estimated_tokens > token_manager.daily_limit:
            # 制限超過時はチャットボットでエラーメッセージを返す
            return {
                "answer": "トークン使用量が制限に達しました。明日までお待ちください。",
                "conversation_id": None,
                "status": "error"
            }
        
        # トークン使用量を記録
        token_manager.track_usage(user_id, estimated_tokens)
        
        # Dify APIを呼び出し
        data = {
            "inputs": {},
            "query": message,
            "user": user_id
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
        
    except Exception as e:
        return {
            "answer": f"エラーが発生しました: {str(e)}",
            "conversation_id": None,
            "status": "error"
        }

if __name__ == "__main__":
    # テスト実行
    result = chat_with_token_limit("test_user_1", "こんにちは")
    print(result.get("answer", "エラーが発生しました")) 