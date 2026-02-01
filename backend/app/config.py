"""
アプリケーション設定

APIキーの読み込み順序:
1. secrets.json ファイル（推奨）
2. 環境変数
3. .env ファイル
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# .envファイルを読み込み（フォールバック用）
load_dotenv()

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
SECRETS_FILE = PROJECT_ROOT / "secrets.json"


def load_secrets() -> dict:
    """secrets.jsonからシークレットを読み込む"""
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: secrets.json の読み込みに失敗しました: {e}")
    return {}


# シークレットを読み込み
_secrets = load_secrets()


def get_secret(key: str, env_var: str | None = None, default: str = "") -> str:
    """
    シークレット値を取得

    優先順位:
    1. secrets.json
    2. 環境変数
    3. デフォルト値
    """
    # secrets.jsonから取得
    if key in _secrets and _secrets[key]:
        return _secrets[key]

    # 環境変数から取得
    if env_var:
        env_value = os.getenv(env_var, "")
        if env_value:
            return env_value

    return default


# APIキー設定
class Settings:
    """アプリケーション設定"""

    # e-Stat API
    ESTAT_APP_ID: str = get_secret("estat_app_id", "ESTAT_APP_ID")

    # 不動産情報ライブラリ API
    REINFOLIB_API_KEY: str = get_secret("reinfolib_api_key", "REINFOLIB_API_KEY")

    # Google Maps API
    GOOGLE_MAPS_API_KEY: str = get_secret("google_maps_api_key", "GOOGLE_MAPS_API_KEY")

    @classmethod
    def reload(cls):
        """設定を再読み込み"""
        global _secrets
        _secrets = load_secrets()
        cls.ESTAT_APP_ID = get_secret("estat_app_id", "ESTAT_APP_ID")
        cls.REINFOLIB_API_KEY = get_secret("reinfolib_api_key", "REINFOLIB_API_KEY")
        cls.GOOGLE_MAPS_API_KEY = get_secret("google_maps_api_key", "GOOGLE_MAPS_API_KEY")

    @classmethod
    def print_status(cls):
        """設定状態を表示"""
        print("=== API設定状態 ===")
        print(f"e-Stat API: {'設定済み' if cls.ESTAT_APP_ID else '未設定'}")
        print(f"不動産情報ライブラリ API: {'設定済み' if cls.REINFOLIB_API_KEY else '未設定'}")
        print(f"Google Maps API: {'設定済み' if cls.GOOGLE_MAPS_API_KEY else '未設定'}")
        print("==================")


settings = Settings()
