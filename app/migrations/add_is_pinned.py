from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

engine = create_engine('sqlite:///./test.db')

def upgrade():
    with engine.connect() as conn:
        try:
            # まず既存のテーブル構造を確認
            result = conn.execute(text("PRAGMA table_info(conversations)"))
            columns = [row[1] for row in result.fetchall()]
            
            # is_pinnedカラムが存在しない場合のみ追加
            if 'is_pinned' not in columns:
                conn.execute(text("""
                    ALTER TABLE conversations 
                    ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                print("Successfully added is_pinned column")
            else:
                print("Column is_pinned already exists")
                
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            conn.rollback()
            raise

if __name__ == "__main__":
    upgrade() 