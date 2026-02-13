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
    raise FileNotFoundError('config.py が見てかりません。')

def take_config(name, required=False):
    return getattr(config, name, None) if not required else getattr(config, name)

app = Flask(__name__)

# --- データベース接続設定 ---
mongo_config = take_config('MONGO', required=True)
client = MongoClient(host=mongo_config['host'])
db = client[mongo_config['database']]

app.secret_key = take_config('SECRET_KEY') or 'change-me'
app.config['SESSION_TYPE'] = 'redis'
redis_config = take_config('REDIS', required=True)
app.config['SESSION_REDIS'] = Redis(
    host=redis_config['CACHE_REDIS_HOST'],
    port=redis_config['CACHE_REDIS_PORT'],
    password=redis_config['CACHE_REDIS_PASSWORD'],
    db=redis_config['CACHE_REDIS_DB']
)

Session(app)
Cache(app, config=redis_config)
CSRFProtect(app)

# --- 設定情報 ---
def get_config():
    # request.host_url を使って現在のドメインを自動取得
    base_url = request.host_url.rstrip('/')
    return {
        'songs_baseurl': f"{base_url}/songs/",
        'assets_baseurl': f"{base_url}/assets/",
        'preview_type': 'mp3',
        'accounts': True,
        'title': 'taiko-web'
    }

# --- ページ配信 ---
@app.route('/')
def route_index():
    # config情報を index.html に渡す
    return render_template('index.html', version={'version': '1.0'}, config=get_config())

# --- API配信 ---
@app.route('/api/config')
def route_api_config():
    return jsonify(get_config())

@app.route('/api/categories')
def route_api_categories():
    return jsonify(list(db.categories.find({}, {'_id': False})))

@app.route('/api/songs')
def route_api_songs():
    return jsonify(list(db.songs.find({'enabled': True}, {'_id': False})))

# --- 静的ファイル配信（これが一番大事です） ---

@app.route('/assets/<path:filename>')
def send_assets(filename):
    # assets フォルダ内のサブフォルダ（img/など）も再帰的に探します
    return send_from_directory('assets', filename)

@app.route('/src/<path:filename>')
def send_src(filename):
    # JavaScriptやCSSを配信します
    return send_from_directory('src', filename)

@app.route('/songs/<path:filename>')
def send_songs(filename):
    # 楽曲データを配信します
    return send_from_directory('songs', filename)

# --- サーバー起動 ---
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    # Render標準の10000番ポートと外部公開用のアドレス0.0.0.0を指定
    parser.add_argument('port', type=int, nargs='?', default=10000)
    parser.add_argument('-b', '--bind-address', default='0.0.0.0')
    args = parser.parse_args()
    
    app.run(host=args.bind_address, port=args.port)
