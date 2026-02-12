import os
import urllib.parse

# 基本設定
ASSETS_BASEURL = '/public/assets/'
SONGS_BASEURL = '/songs/'
MULTIPLAYER_URL = ''
EMAIL = None
ACCOUNTS = False  # データベース接続を安定させるため一旦 False にします
CUSTOM_JS = ''
PLUGINS = [{'url': '', 'start': False, 'hide': False}]
PREVIEW_TYPE = 'mp3'

# --- MongoDB 設定 ---
# RenderのEnvironmentで設定した MONGO_HOST を読み込みます
MONGO = {
    'host': [os.environ.get('MONGO_HOST', '127.0.0.1:27017')],
    'database': 'taiko'
}

# --- Redis 設定 ---
# RenderのEnvironmentで設定した REDIS_URL を読み込み、分解して設定します
redis_url_str = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379')
redis_url = urllib.parse.urlparse(redis_url_str)

REDIS = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': redis_url.hostname,
    'CACHE_REDIS_PORT': redis_url.port or 6379,
    'CACHE_REDIS_PASSWORD': redis_url.password,
    'CACHE_REDIS_DB': 0
}

# セキュリティ設定
SECRET_KEY = os.environ.get('SECRET_KEY', 'shirasu-taiko-key-12345')
URL = 'https://github.com/bui/taiko-web/'

# Google Drive API (無効)
GOOGLE_CREDENTIALS = {
    'gdrive_enabled': False,
    'api_key': '',
    'oauth_client_id': '',
    'project_number': '',
    'min_level': None
}
