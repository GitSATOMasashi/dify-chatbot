from dotenv import load_dotenv
import os

# .envファイルから環境変数を読み込む
load_dotenv()

# APIキーを取得
DIFY_API_KEY = os.getenv('DIFY_API_KEY')

# APIキーが存在しない場合のエラーハンドリング
if not DIFY_API_KEY:
    raise ValueError(".envファイルにDIFY_API_KEYを設定してください") 