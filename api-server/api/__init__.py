"""
Main application package

"""
import json
import psycopg2
from flask import Flask, g

app = Flask(__name__)

from api import index

with open('api/api.config', 'rt') as f:
    config = json.loads(f.read())

@app.before_request
def get_db():
    retry_count = 10

    if not hasattr(g, 'conn'):
        while retry_count > 0:
            try:
                g.conn = psycopg2.connect(config['db']['dsn'])
                g.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                return
            except psycopg2.OperationalError:
                print("Could not connect to database, retry_count = %s" % retry_count)
                time.sleep(10)
                retry_count = retry_count - 1
            raise Exception("Could not establish connection to database")

@app.teardown_appcontext
def teardown(exception):
    if hasattr(g, 'conn'):
        g.conn.close()
