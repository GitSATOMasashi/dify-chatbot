from datetime import datetime

class TokenService:
    def __init__(self, db):
        self.db = db
    
    async def check_token_limit(self, user_id: str, tokens: int):
        """トークン制限のチェック"""
        today = datetime.now().date()
        current_usage = await self.get_daily_usage(user_id, today)
        user_limit = await self.get_user_limit(user_id)
        
        if current_usage + tokens > user_limit:
            raise TokenLimitExceeded("1日の制限を超過しました") 