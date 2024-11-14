from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from . import database
from datetime import datetime
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import tiktoken

load_dotenv()

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルの提供
app.mount("/static", StaticFiles(directory="static"), name="static")

class MessageRequest(BaseModel):
    message: str
    user_id: str

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def count_tokens(text: str) -> int:
    """tiktokenを使用して正確なトークン数を計算"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

@app.get("/tokens/{user_id}")
def get_tokens(user_id: str, db: Session = Depends(get_db)):
    usage = db.query(database.TokenUsage).filter(
        database.TokenUsage.user_id == user_id
    ).first()
    
    if not usage:
        usage = database.TokenUsage(user_id=user_id, remaining_tokens=200)
        db.add(usage)
        db.commit()
        db.refresh(usage)
    
    return {"remaining_tokens": usage.remaining_tokens}

@app.post("/chat")
def send_message(request: MessageRequest, db: Session = Depends(get_db)):
    # 入力のトークン数を計算
    input_tokens = count_tokens(request.message)
    estimated_response_tokens = input_tokens * 2  # 初期見積もり
    required_tokens = input_tokens + estimated_response_tokens
    
    usage = db.query(database.TokenUsage).filter(
        database.TokenUsage.user_id == request.user_id
    ).first()
    
    if not usage:
        usage = database.TokenUsage(user_id=request.user_id, remaining_tokens=200)
        db.add(usage)
        db.commit()
        db.refresh(usage)
    
    # 必要なトークン数をチェック
    if usage.remaining_tokens < required_tokens:
        raise HTTPException(
            status_code=403, 
            detail="トークンが不足しています"
        )
    
    # 入力トークンのみ先に消費
    usage.remaining_tokens -= input_tokens
    db.commit()
    
    return {
        "status": "success",
        "remaining_tokens": usage.remaining_tokens,
        "input_tokens": input_tokens
    }

@app.post("/chat/response")
async def record_response(
    response: dict,  # JSONとして受け取るように変更
    db: Session = Depends(get_db)
):
    response_text = response.get('response')
    user_id = response.get('user_id')
    
    if not response_text or not user_id:
        raise HTTPException(status_code=400, detail="Missing response text or user_id")
    
    response_tokens = count_tokens(response_text)
    
    usage = db.query(database.TokenUsage).filter(
        database.TokenUsage.user_id == user_id
    ).first()
    
    if usage:
        usage.remaining_tokens -= response_tokens
        db.commit()
    
    return {
        "status": "success",
        "remaining_tokens": usage.remaining_tokens,
        "response_tokens": response_tokens
    }

@app.post("/tokens/reset/{user_id}")
def reset_tokens(user_id: str, db: Session = Depends(get_db)):
    usage = db.query(database.TokenUsage).filter(
        database.TokenUsage.user_id == user_id
    ).first()
    
    if usage:
        usage.remaining_tokens = 200
        usage.last_updated = datetime.utcnow()
    else:
        usage = database.TokenUsage(user_id=user_id, remaining_tokens=200)
        db.add(usage)
    
    db.commit()
    db.refresh(usage)
    
    return {"message": "Tokens reset successfully", "remaining_tokens": usage.remaining_tokens}

@app.get("/api/config")
async def get_config():
    return {
        "api_key": os.getenv("DIFY_API_KEY")
    }