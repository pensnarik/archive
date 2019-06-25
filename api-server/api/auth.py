# *-* coding: utf-8 -*-

# Autots REST API realization

import os
import json
import base64
from functools import wraps

from flask import request
from api import app, sql

from api.common import DecimalEncoder

def check_token(token):
    return sql.get_value('select app.check_token(%s)', (token,))

def api_error(code, message):
    resp = app.response_class(
        response=json.dumps({'status': 'error', 'message': message}, cls=DecimalEncoder),
        status=code,
        mimetype='application/json'
    )

    return resp

def api_return(data, status=200):
    resp = app.response_class(
        response=json.dumps(data, cls=DecimalEncoder, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

    return resp

def api_auth_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            token = request.headers['Authorization'].split(' ')[1]
        except KeyError:
            return api_error(403, 'Need auth')

        if not check_token(token):
            return api_error(403, 'Invalid or expired token')

        return func(*args, **kwargs)
    return decorated_view
