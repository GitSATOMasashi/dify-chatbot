from datetime import datetime
from .database import TokenDatabase

class TokenManager:
    def __init__(self, daily_limit=1000):
        self.db = TokenDatabase()
        self.daily_limit = daily_limit
    
    def get_daily_usage(self, user_id: str) -> int:
        """ユーザーの今日のトークン使用量を取得"""
        today = datetime.now().date()
        cursor = self.db.conn.cursor()
        
        cursor.execute('''
            SELECT tokens_used FROM token_usage 
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def track_usage(self, user_id: str, tokens: int):
        """トークン使用量を記録"""
        today = datetime.now().date()
        current_usage = self.get_daily_usage(user_id)
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO token_usage (user_id, date, tokens_used)
            VALUES (?, ?, ?)
        ''', (user_id, today, current_usage + tokens))
        
        self.db.conn.commit() 