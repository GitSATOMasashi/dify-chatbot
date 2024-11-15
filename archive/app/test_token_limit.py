from token_manager import TokenManager
from config import DIFY_API_KEY
import requests
from datetime import datetime

class TokenLimitTester:
    def __init__(self):
        self.token_manager = TokenManager(daily_limit=100)  # テスト用に低めの制限値を設定
        self.test_user = "test_user_1"
        
    def test_basic_chat(self):
        """基本的なチャット機能のテスト"""
        print("1. 基本的なチャットテスト")
        response = self.send_message("こんにちは")
        print(f"応答: {response}\n")
        
    def test_token_limit(self):
        """トークン制限のテスト"""
        print("2. トークン制限テスト")
        # 制限に近い長いメッセージを送信
        long_message = "あ" * 400  # 約100トークン相当
        response = self.send_message(long_message)
        print(f"長いメッセージの応答: {response}\n")
        
        # 制限を超えるメッセージを送信
        print("3. 制限超過テスト")
        response = self.send_message(long_message)  # 2回目で制限超過
        print(f"制限超過時の応答: {response}\n")
        
    def send_message(self, message: str):
        url = 'https://api.dify.ai/v1/chat-messages'
        headers = {
            'Authorization': f'Bearer {DIFY_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            "inputs": {},
            "query": message,
            "user": self.test_user
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    tester = TokenLimitTester()
    
    print("=== トークン制限機能テスト開始 ===\n")
    
    # 基本的なチャットテスト
    tester.test_basic_chat()
    
    # トークン制限テスト
    tester.test_token_limit()
    
    print("=== テスト完了 ===") 