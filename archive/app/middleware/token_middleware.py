from fastapi import Request, Response, JSONResponse
from app.services.token_service import TokenService, TokenLimitExceeded

class TokenLimitMiddleware:
    def __init__(self, token_service):
        self.token_service = token_service
    
    async def process_request(self, request):
        user_id = request.user.id
        try:
            await self.token_service.check_token_limit(user_id, request.estimated_tokens)
        except TokenLimitExceeded:
            return JSONResponse(
                status_code=429,
                content={"error": "トークン制限に達しました"}
            ) 