import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

@app.after_request
def add_header(response):
    if response.mimetype in ['application/javascript', 'text/html']:
        response.charset = 'utf-8'
    return response

@app.route('/')
def index():
    config = {'assets_baseurl': '/assets/', 'songs_baseurl': '/songs/', 'gdrive_enabled': False}
    return render_template('index.html', config=config, version={'commit_short': 'rev-1', 'version': '1.0', 'url': '#'})

@app.route('/assets/<path:path>')
def send_assets(path): return send_from_directory('assets', path)

@app.route('/src/<path:path>')
def send_src(path): return send_from_directory('src', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
