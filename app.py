#!/usr/bin/env python3

import base64
import bcrypt
import hashlib
try:
    import config
except ModuleNotFoundError:
    raise FileNotFoundError('No such file or directory: \'config.py\'. Copy the example config file config.example.py to config.py')
import json
import re
import requests
import schema
import os
import time

from functools import wraps
from flask import Flask, g, jsonify, render_template, request, abort, redirect, session, flash, make_response, send_from_directory
from flask_caching import Cache
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError
from ffmpy import FFmpeg
from pymongo import MongoClient
from redis import Redis

def take_config(name, required=False):
    if hasattr(config, name):
        return getattr(config, name)
    elif required:
        raise ValueError('Required option is not defined in the config.py file: {}'.format(name))
    else:
        return None

app = Flask(__name__)

# MongoDB接続設定
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
app.cache = Cache(app, config=redis_config)
sess = Session()
sess.init_app(app)
csrf = CSRFProtect(app)

db.users.create_index('username', unique=True)
db.songs.create_index('id', unique=True)
db.scores.create_index('username')

def get_config(credentials=False):
    config_out = {
        'songs_baseurl': take_config('SONGS_BASEURL', required=True),
        'assets_baseurl': take_config('ASSETS_BASEURL', required=True),
        'email': take_config('EMAIL'),
        'accounts': take_config('ACCOUNTS'),
        'custom_js': take_config('CUSTOM_JS'),
        'plugins': take_config('PLUGINS') and [x for x in take_config('PLUGINS') if x['url']],
        'preview_type': take_config('PREVIEW_TYPE') or 'mp3',
        'multiplayer_url': take_config('MULTIPLAYER_URL')
    }
    # 配信URLをRenderの環境に合わせる
    if not config_out.get('songs_baseurl'):
        config_out['songs_baseurl'] = request.host_url + 'songs/'
    if not config_out.get('assets_baseurl'):
        config_out['assets_baseurl'] = request.host_url + 'assets/'
    
    config_out['_version'] = {'commit': None, 'commit_short': '', 'version': None, 'url': take_config('URL')}
    return config_out

@app.route('/')
def route_index():
    return render_template('index.html', version={'version': None}, config=get_config())

# --- 足りなかった API の追加 ---
@app.route('/api/categories')
@app.cache.cached(timeout=15)
def route_api_categories():
    categories = list(db.categories.find({},{'_id': False}))
    return jsonify(categories)

@app.route('/api/songs')
@app.cache.cached(timeout=15)
def route_api_songs():
    songs = list(db.songs.find({'enabled': True}, {'_id': False}))
    return jsonify(songs)

@app.route('/api/config')
@app.cache.cached(timeout=15)
def route_api_config():
    return jsonify(get_config(credentials=True))

@app.route('/api/csrftoken')
def route_csrftoken():
    return jsonify({'status': 'ok', 'token': generate_csrf()})

# --- 静的ファイル配信 (サブフォルダ img/ などに完全対応) ---
@app.route('/src/<path:filename>')
def send_src(filename):
    return send_from_directory('src', filename)

@app.route('/assets/<path:filename>')
def send_assets(filename):
    # assets/img/... などの深い階層もこれで読み込めます
    return send_from_directory('assets', filename)

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
