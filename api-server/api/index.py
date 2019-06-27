import json
from flask import Response, request, jsonify
from datetime import datetime

from api import app, sql
from api.auth import api_auth_required

def get_timestamp(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    return Response('OK', mimetype='text/plain')

def add_files_recursively(data, parent):
    query = "select app.file_add(%(md5)s, %(size)s, %(filetype)s, %(mtime)s, %(ctime)s, %(filename)s, %(parent)s)"
    query_image = "select app.image_add(%(file_id)s, %(width)s, %(height)s, %(pcp_hash)s, %(coords)s, " \
                  "%(exif_datetime)s, %(format)s, %(mode)s, %(exif)s)"
    id = None

    for hash in data.keys():
        if data[hash]['size'] == 0: continue

        mtime = get_timestamp(data[hash]['mtime'])
        ctime = get_timestamp(data[hash]['ctime'])

        args = {'md5': hash, 'size': data[hash]['size'], 'filetype': data[hash]['filetype'],
                'mtime': mtime, 'ctime': ctime,
                'filename': data[hash]['filename'], 'parent': parent}

        id = sql.get_value(query, args)

        if data[hash]['filetype'] == 'image':
            if 'latlon' in data[hash]:
                coords = '(%s)' % ','.join([str(i) for i in data[hash]['latlon']])
            else:
                coords = None
            sql.execute(query_image,
                        {'file_id': id, 'width': data[hash]['width'], 'height': data[hash]['height'],
                         'pcp_hash': data[hash]['pcp_hash'], 'coords': coords,
                         'exif_datetime': data[hash].get('exif_datetime'),
                         'format': data[hash]['format'], 'mode': data[hash]['mode'],
                         'exif': json.dumps(data[hash]['exif'], ensure_ascii=False)})

        if 'included_files' in data[hash]:
            add_files_recursively(data[hash]['included_files'], hash)

    return id

@app.route('/api/add', methods=['POST'])
@api_auth_required
def file_add():
    content = request.json
    id = add_files_recursively(content, None)
    return jsonify({'status': 'ok', 'id': id})

@app.route('/api/check/<string:hash>', methods=['GET'])
@api_auth_required
def file_check(hash):
    result = sql.get_value('select app.file_exists(%s)', [hash])
    return jsonify({'status': 'ok', 'result': result})

@app.route('/api/image/list', methods=['POST'])
@api_auth_required
def image_list():
    filters = request.json
    result = sql.get_rows('select * from app.image_list(%s, %s)', [filters['filter'], filters['value']])
    return jsonify({'status': 'ok', 'files': result})

@app.route('/api/image/local_filename/<string:hash>', methods=['GET'])
@api_auth_required
def image_original_filename(hash):
    result = sql.get_value('select app.image_local_filename(%s)', [hash])
    return jsonify({'status': 'ok', 'filename': result})

@app.route('/api/image/getattr/<string:hash>', methods=['GET'])
@api_auth_required
def image_getattr(hash):
    result = sql.get_row('select * from app.image_getattr(%s)', [hash])
    return jsonify({'status': 'ok', 'attrs': result})

@app.route('/api/backup', methods=['POST'])
@api_auth_required
def backup():
    payload = request.json
    result = sql.get_value('select app.file_backup(%s, %s, %s)', [payload['hash'], payload['service'],
                                                                  payload['uid']])
    return jsonify({'status': 'ok', 'id': result})
