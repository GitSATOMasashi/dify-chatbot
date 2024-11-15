from sqlalchemy import create_engine
from app.database import Base
import os

# データベースファイルが存在する場合は削除
if os.path.exists("test.db"):
    os.remove("test.db")

# エンジンを作成
engine = create_engine('sqlite:///./test.db')

# テーブルを作成
Base.metadata.create_all(bind=engine)

print("Database initialized successfully!") 