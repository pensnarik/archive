import json
from flask import Response, request

from api import app, sql

@app.route('/')
def index():
    return Response('OK', mimetype='text/plain')

@app.route('/api/add', methods=['POST'])
def file_add():
    content = request.json
    id = sql.get_value('select app.file_add(%s, %s, %s)', [content['filename'], 100, 'text'])
    return str(id)
