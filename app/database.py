from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./tokens.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# トークン管理用のモデル
class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    remaining_tokens = Column(Integer, default=200)
    last_updated = Column(DateTime, default=datetime.utcnow)

# データベース作成
Base.metadata.create_all(bind=engine) 