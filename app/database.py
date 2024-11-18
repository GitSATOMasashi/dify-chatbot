from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_pinned = Column(Boolean, default=False)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer)
    content = Column(String)
    role = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    remaining_tokens = Column(Integer, default=200)
    last_updated = Column(DateTime, default=datetime.utcnow)

# データベース接続のための依存関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 