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

def hi( ):
    #results = engine.execute('INSERT INTO beverage_transaction (barcode, transaction_date) VALUES(SHA1(NOW()), NOW() );');
    results = engine.execute('SELECT COUNT(consumed.id) AS amount, consumable.upc, consumable.name FROM consumed, consumable WHERE consumable.id=consumed.consumable_id GROUP BY name;');
    out = '<html><head><script type="text/javascript" src="../src/plugins/jqplot.pieRenderer.min.js"></script><script type="text/javascript" src="../src/plugins/jqplot.donutRenderer.min.js"></script></head><body><table>'
    for row in results:
        url = 'http://www.upcdatabase.com/item/'+row['upc']
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        the_page = response.read()
        the_page = the_page[the_page.index('<td>Description'):];
        out += '<tr><td>Count:</td><td>'+str(row['amount'])+'</td>'+the_page[:the_page.index('</tr>')]+'</tr>';
    
    results.close()
    out += "</table></body></html>"
#    return the_page[:the_page.index('</tr>')];
    return Markup(out)
#    return render_template('hi.html', message='message text')

if __name__ == '__main__':
    app.run(debug=True)

