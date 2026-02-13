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

# --- データベース接続 ---
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

# --- 設定情報（ここを修正しました） ---
def get_config():
    # Render環境では末尾のスラッシュが重要です
    return {
        'songs_baseurl': '/songs/',
        'assets_baseurl': '/assets/',
        'preview_type': 'mp3',
        'accounts': True,
        'title': 'taiko-web'
    }

@app.route('/')
def route_index():
    return render_template('index.html', version={'version': '1.0'}, config=get_config())

# --- API ---
@app.route('/api/config')
def route_api_config():
    return jsonify(get_config())

@app.route('/api/categories')
def route_api_categories():
    return jsonify(list(db.categories.find({}, {'_id': False})))

@app.route('/api/songs')
def route_api_songs():
    return jsonify(list(db.songs.find({'enabled': True}, {'_id': False})))

# --- 静的ファイル配信 ---

@app.route('/assets/<path:filename>')
def send_assets(filename):
    # ルートにある assets フォルダから配信
    return send_from_directory('assets', filename)

@app.route('/src/<path:filename>')
def send_src(filename):
    # ルートにある src フォルダから配信
    return send_from_directory('src', filename)

@app.route('/songs/<path:filename>')
def send_songs(filename):
    return send_from_directory('songs', filename)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, nargs='?', default=10000)
    parser.add_argument('-b', '--bind-address', default='0.0.0.0')
    args = parser.parse_args()
    app.run(host=args.bind_address, port=args.port)
