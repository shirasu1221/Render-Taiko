#!/usr/bin/env python3
import os
from flask import Flask, jsonify, render_template, request, send_from_directory
from pymongo import MongoClient
from redis import Redis
from flask_session import Session
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

try:
    import config
except ImportError:
    raise FileNotFoundError('config.py が見つかりません。')

def take_config(name, required=False):
    return getattr(config, name, None) if not required else getattr(config, name)

app = Flask(__name__)

# --- 文字化け対策（すべてのレスポンスをUTF-8に強制） ---
@app.after_request
def add_header(response):
    if response.mimetype == 'application/javascript' or response.mimetype == 'text/html':
        response.charset = 'utf-8'
    return response

# --- データベース接続 ---
mongo_config = take_config('MONGO', required=True)
client = MongoClient(host=mongo_config['host'])
db = client[mongo_config['database']]
app.secret_key = take_config('SECRET_KEY') or 'change-me'
app.config['SESSION_TYPE'] = 'redis'
redis_config = take_config('REDIS', required=True)
app.config['SESSION_REDIS'] = Redis(host=redis_config['CACHE_REDIS_HOST'], port=redis_config['CACHE_REDIS_PORT'], password=redis_config['CACHE_REDIS_PASSWORD'], db=redis_config['CACHE_REDIS_DB'])
Session(app)
Cache(app, config=redis_config)
CSRFProtect(app)

# --- 設定情報（JSに渡すデータ） ---
def get_config():
    return {
        'songs_baseurl': '/songs/',
        'assets_baseurl': '/assets/',
        'preview_type': 'mp3',
        'accounts': True,
        'title': '太鼓ウェブ - Taiko Web',
        'gdrive_enabled': False,
        'google_credentials': {
            'gdrive_enabled': False
        },
        'multiplayer': False,
        'multiplayer_url': '',
        '_version': {
            'commit_short': 'rev-1',
            'version': '1.0'
        }
    }

@app.route('/')
def route_index():
    conf = get_config()
    version_info = {
        'commit_short': 'rev-1',
        'version': '1.0',
        'url': 'https://github.com/shirasu1221/Render-Taiko'
    }
    return render_template('index.html', version=version_info, config=conf)

@app.route('/api/config')
def route_api_config():
    return jsonify(get_config())

@app.route('/api/categories')
def route_api_categories():
    return jsonify(list(db.categories.find({}, {'_id': False})))

@app.route('/api/songs')
def route_api_songs():
    return jsonify(list(db.songs.find({'enabled': True}, {'_id': False})))

@app.route('/api/scores/get')
def route_api_scores_get():
    return jsonify([])

@app.route('/assets/<path:filename>')
def send_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/src/<path:filename>')
def send_src(filename):
    return send_from_directory('src', filename)

@app.route('/songs/<path:filename>')
def send_songs(filename):
    return send_from_directory('songs', filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
