import sqlite3
from datetime import datetime

def check_database():
    try:
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        
        print("\n=== Database Tables ===")
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        print("Tables:", tables)
        
        print("\n=== Conversations Table ===")
        c.execute("""
            SELECT id, user_id, title, last_message, created_at 
            FROM conversations 
            ORDER BY created_at DESC;
        """)
        conversations = c.fetchall()
        for conv in conversations:
            print("\nConversation:")
            print(f"ID: {conv[0]}")
            print(f"User ID: {conv[1]}")
            print(f"Title: {conv[2]}")
            print(f"Last Message: {conv[3]}")
            print(f"Created At: {conv[4]}")
        
        print("\n=== Messages Table ===")
        c.execute("""
            SELECT id, content, role, user_id, conversation_id, created_at 
            FROM messages 
            ORDER BY created_at DESC;
        """)
        messages = c.fetchall()
        for msg in messages:
            print("\nMessage:")
            print(f"ID: {msg[0]}")
            print(f"Content: {msg[1]}")
            print(f"Role: {msg[2]}")
            print(f"User ID: {msg[3]}")
            print(f"Conversation ID: {msg[4]}")
            print(f"Created At: {msg[5]}")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()
