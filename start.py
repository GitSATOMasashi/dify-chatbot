import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", "8000"))
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=False
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        port = 8000
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=False
        ) 