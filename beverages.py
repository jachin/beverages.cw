from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import sqlite3
from contextlib import closing
import urllib2
import simplejson
from pprint import pprint
import sqlalchemy
from sqlalchemy import *

import settings

# create our little application :)
app = Flask(__name__)
app.config.from_object(settings.DevelopmentConfig)
#app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
        for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    g.db.close()


@app.route('/')
def show_stats():
    return 'Beverage-o-meter'


@app.route('/update_db/')
def update_database():
    req = urllib2.Request("http://192.168.22.193")
    opener = urllib2.build_opener()
    f = opener.open(req)
    scans = simplejson.load(f)
    
    for scan in scans:
        if is_new_consumable(scan['upc']):
            add_new_consumable(scan['upc'])
        if is_new_consumed(scan['id']):
            add_new_consumed(scan['id'],scan['timestamp'],scan['upc'])

    return 'Database updated.'


if __name__ == '__main__':
    app.run(debug=True)

