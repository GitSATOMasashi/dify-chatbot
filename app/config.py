from dotenv import load_dotenv
import os

# .envファイルから環境変数を読み込む
load_dotenv()

# 必須の環境変数をチェック
def get_dify_api_keys():
    default_key = os.getenv('DIFY_API_KEY')
    if not default_key:
        raise ValueError(".envファイルにDIFY_API_KEYを設定してください")
    
    return {
        'default': default_key,
        'bot2': os.getenv('DIFY_API_KEY_2', default_key),  # なければdefault_keyを使用
        'bot3': os.getenv('DIFY_API_KEY_3', default_key)   # なければdefault_keyを使用
    }

DIFY_API_KEYS = get_dify_api_keys() 