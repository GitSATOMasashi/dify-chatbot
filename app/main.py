from fastapi import FastAPI, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from . import database
from datetime import datetime
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import tiktoken
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
import logging
from typing import Optional
from fastapi.responses import JSONResponse
import traceback  # スタックトレース用

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

# ルートパスでindex.htmlを提供
@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

class MessageRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[int] = None

class MessageSave(BaseModel):
    content: str
    role: str
    conversation_id: int
    user_id: str

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def count_tokens(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens: {str(e)}")
        return len(text) // 4  # フォールバック：簡易的な推定

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/tokens/{user_id}")
def get_remaining_tokens(user_id: str, db: Session = Depends(get_db)):
    try:
        token_usage = db.query(database.TokenUsage).filter(
            database.TokenUsage.user_id == user_id
        ).first()
        
        logger.info(f"Token check for user {user_id}: {token_usage}")
        
        if not token_usage:
            # 新規ユーザーの場合は初期トークンを設定
            token_usage = database.TokenUsage(user_id=user_id)
            db.add(token_usage)
            db.commit()
            db.refresh(token_usage)
            logger.info(f"Created new token usage for user {user_id}")
        
        return {"remaining_tokens": token_usage.remaining_tokens}
        
    except Exception as e:
        logger.error(f"Error in get_remaining_tokens: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{user_id}")
def get_conversations(user_id: str, db: Session = Depends(get_db)):
    try:
        conversations = db.query(database.Conversation).filter(
            database.Conversation.user_id == user_id
        ).order_by(
            database.Conversation.is_pinned.desc(),  # ピン留めを優先
            database.Conversation.created_at.desc()
        ).all()
        
        logger.info(f"Found {len(conversations)} conversations for user {user_id}")
        
        return [{
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
            "is_pinned": conv.is_pinned
        } for conv in conversations]
        
    except Exception as e:
        logger.error(f"Error in get_conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    """特定の会話のメッセージを取得"""
    messages = db.query(database.Message).filter(
        database.Message.conversation_id == conversation_id
    ).order_by(database.Message.created_at).all()
    
    return [{
        "content": msg.content,
        "role": msg.role,
        "created_at": msg.created_at
    } for msg in messages]

@app.post("/chat")
async def chat(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        message_request = MessageRequest(
            user_id=data.get("user_id", "test_user"),
            message=data.get("message", ""),
            conversation_id=data.get("conversation_id")
        )
        
        logger.info(f"Processing chat request for user {message_request.user_id}")
        
        # 入力のトークン数を計算
        input_tokens = count_tokens(message_request.message)
        estimated_response_tokens = input_tokens * 2  # 初期見積もり
        required_tokens = input_tokens + estimated_response_tokens
        
        # トークン使用量をチェック
        usage = db.query(database.TokenUsage).filter(
            database.TokenUsage.user_id == message_request.user_id
        ).first()
        
        if not usage:
            usage = database.TokenUsage(user_id=message_request.user_id, remaining_tokens=200)
            db.add(usage)
            db.commit()
            db.refresh(usage)
        
        # 必要なトークン数をチェック
        if usage.remaining_tokens < required_tokens:
            logger.warning(f"Insufficient tokens for user {message_request.user_id}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Insufficient tokens. Please reset your tokens."}
            )
        
        # トークンを消費
        usage.remaining_tokens -= input_tokens
        db.commit()
        
        # 会話を取得または作成
        conversation = db.query(database.Conversation).filter(
            database.Conversation.user_id == message_request.user_id
        ).order_by(database.Conversation.created_at.desc()).first()
        
        if not conversation:
            conversation = database.Conversation(
                user_id=message_request.user_id,
                title=message_request.message[:30] + "..."
            )
            db.add(conversation)
            db.commit()
        
        # メッセージを保存
        message = database.Message(
            conversation_id=conversation.id,
            content=message_request.message,
            role="user"
        )
        db.add(message)
        db.commit()
        
        logger.info(f"Successfully processed message for conversation {conversation.id}")
        
        return {
            "status": "success",
            "remaining_tokens": usage.remaining_tokens,
            "input_tokens": input_tokens,
            "conversation_id": conversation.id
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())  # スタックトレースを記録
        
        # エラーレスポンスを返す
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

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

@app.post("/messages")
def save_message(request: MessageSave, db: Session = Depends(get_db)):
    """メッセージを保存"""
    message = database.Message(
        conversation_id=request.conversation_id,
        content=request.content,
        role=request.role
    )
    db.add(message)
    db.commit()
    
    return {"status": "success"}

@app.post("/conversations/new")
def create_new_conversation(request: dict, db: Session = Depends(get_db)):
    """新しい会話を作成"""
    conversation = database.Conversation(
        user_id=request.get('user_id'),
        title="新しいトーク"  # 初期タイトル
    )
    db.add(conversation)
    db.commit()
    
    return {
        "status": "success",
        "conversation_id": conversation.id
    }

@app.put("/conversations/{conversation_id}/title")
def update_conversation_title(
    conversation_id: int, 
    title_data: dict, 
    db: Session = Depends(get_db)
):
    print(f"Updating title for conversation {conversation_id}")
    print(f"Title data: {title_data}")
    
    try:
        # 会話を取得
        conversation = db.query(database.Conversation).filter(
            database.Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            print(f"Conversation {conversation_id} not found")
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # manual_update フラグがある場合のみ、または
        # タイトルが "新しいチャット" の場合のみ更新を許可
        if title_data.get("manual_update", False) or conversation.title == "新しいチャット":
            new_title = title_data.get("title")
            print(f"New title: {new_title}")
            conversation.title = new_title
            
            try:
                db.commit()
                print("Title updated successfully")
            except Exception as commit_error:
                print(f"Commit error: {str(commit_error)}")
                db.rollback()
                raise
        else:
            print("Title update skipped - not a manual update")
            
        return {"status": "success", "title": conversation.title}
            
    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    try:
        # 会話を取得
        conversation = db.query(database.Conversation).filter(
            database.Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # 関連するメッセージも削除
        db.query(database.Message).filter(
            database.Message.conversation_id == conversation_id
        ).delete()
        
        # 会話を削除
        db.delete(conversation)
        db.commit()
        
        return {"status": "success"}
            
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/conversations/{conversation_id}/pin")
async def toggle_pin(conversation_id: int, db: Session = Depends(get_db)):
    try:
        conversation = db.query(database.Conversation).filter(
            database.Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # ピン留め状態を切り替え
        conversation.is_pinned = not conversation.is_pinned
        db.commit()
        
        return {
            "status": "success",
            "is_pinned": conversation.is_pinned
        }
            
    except Exception as e:
        db.rollback()
        print(f"Error in toggle_pin: {str(e)}")  # デバッグ用
        raise HTTPException(status_code=500, detail=str(e))
port = int(os.getenv("PORT", 8000))

# データベースの設定
DATABASE_URL = "sqlite+aiosqlite:///./test.db"  # 既存のDBと同じパスを使用

# 非同期ンジンとセッションの作成
async_engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
