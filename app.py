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

app = Flask(__name__, template_folder='templates') # templatesフォルダを明示

# MongoDB接続
mongo_config = take_config('MONGO', required=True)
client = MongoClient(host=mongo_config['host'])
db = client[mongo_config['database']]

# Session & Cache 設定
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

def get_config():
    base_url = request.host_url
    return {
        'songs_baseurl': base_url + 'songs/',
        'assets_baseurl': base_url + 'assets/',
        'preview_type': 'mp3',
        'accounts': True
    }

@app.route('/')
def route_index():
    return render_template('index.html', version={'version': '1.0'}, config=get_config())

# --- API関連 ---
@app.route('/api/config')
def route_api_config():
    return jsonify(get_config())

@app.route('/api/categories')
def route_api_categories():
    return jsonify(list(db.categories.find({}, {'_id': False})))

@app.route('/api/songs')
def route_api_songs():
    return jsonify(list(db.songs.find({'enabled': True}, {'_id': False})))

# --- 【最重要】静的ファイルの配信設定 ---

@app.route('/assets/<path:filename>')
def send_assets(filename):
    # assets フォルダから再帰的にファイルを探します
    return send_from_directory('assets', filename)

@app.route('/src/<path:filename>')
def send_src(filename):
    # src フォルダ（js, css等）を配信します
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
