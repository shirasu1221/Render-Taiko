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

class HashException(Exception):
    pass

def api_error(message):
    return jsonify({'status': 'error', 'message': message})

def generate_hash(id, form):
    md5 = hashlib.md5()
    if form['type'] == 'tja':
        urls = ['%s%s/main.tja' % (take_config('SONGS_BASEURL', required=True), id)]
    else:
        urls = []
        for diff in ['easy', 'normal', 'hard', 'oni', 'ura']:
            if form['course_' + diff]:
                urls.append('%s%s/%s.osu' % (take_config('SONGS_BASEURL', required=True), id, diff))

    for url in urls:
        if url.startswith("http://") or url.startswith("https://"):
            resp = requests.get(url)
            if resp.status_code != 200:
                raise HashException('Invalid response from %s (status code %s)' % (resp.url, resp.status_code))
            md5.update(resp.content)
        else:
            if url.startswith("/"):
                url = url[1:]
            path = os.path.normpath(url)
            if not os.path.isfile(path):
                raise HashException("File not found: %s" % (os.path.abspath(path)))
            with open(path, "rb") as file:
                md5.update(file.read())

    return base64.b64encode(md5.digest())[:-2].decode('utf-8')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('username'):
            return api_error('not_logged_in')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(level):
    def decorated_function(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not session.get('username'):
                return abort(403)
            user = db.users.find_one({'username': session.get('username')})
            if user['user_level'] < level:
                return abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorated_function

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return api_error('invalid_csrf')

@app.before_request
def before_request_func():
    if session.get('session_id'):
        if not db.users.find_one({'session_id': session.get('session_id')}):
            session.clear()

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
    if not config_out.get('songs_baseurl'):
        config_out['songs_baseurl'] = ''.join([request.host_url, 'songs']) + '/'
    if not config_out.get('assets_baseurl'):
        config_out['assets_baseurl'] = ''.join([request.host_url, 'assets']) + '/'
    config_out['_version'] = get_version()
    return config_out

def get_version():
    return {'commit': None, 'commit_short': '', 'version': None, 'url': take_config('URL')}

def get_db_don(user):
    don_body_fill = user.get('don_body_fill', '#5fb7c1')
    don_face_fill = user.get('don_face_fill', '#ff5724')
    return {'body_fill': don_body_fill, 'face_fill': don_face_fill}

@app.route('/')
def route_index():
    return render_template('index.html', version=get_version(), config=get_config())

@app.route('/api/songs')
@app.cache.cached(timeout=15)
def route_api_songs():
    songs = list(db.songs.find({'enabled': True}, {'_id': False}))
    return jsonify(songs)

@app.route('/api/config')
@app.cache.cached(timeout=15)
def route_api_config():
    return jsonify(get_config(credentials=True))

# --- 静的ファイル配信設定 (サブフォルダ対応版) ---

@app.route('/src/<path:filename>')
def send_src(filename):
    # ルート直下の src フォルダから配信
    return send_from_directory('src', filename)

@app.route('/assets/<path:filename>')
def send_assets(filename):
    # ルート直下の assets フォルダから配信 (img/ などのサブフォルダも含む)
    return send_from_directory('assets', filename)

@app.route('/songs/<path:filename>')
def send_songs(filename):
    return send_from_directory('songs', filename)

# --- サーバー起動設定 ---

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    # Renderのポート10000番と外部接続0.0.0.0に対応
    parser.add_argument('port', type=int, nargs='?', default=10000)
    parser.add_argument('-b', '--bind-address', default='0.0.0.0')
    args = parser.parse_args()

    print(f"--- GOGOGO TAIKO STARTING ON PORT {args.port} ---")
    app.run(host=args.bind_address, port=args.port)
