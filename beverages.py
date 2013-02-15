import urllib2
import simplejson
from pprint import pprint
from datetime import datetime

from factual import Factual

from flask import Flask, request, session, url_for, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy

from contextlib import closing

from models import db, app, Consumable, Consumed
from database import db_session

@app.route('/')
def show_stats():
    return 'Beverage-o-meter'


@app.route('/update_db/')
def update_database():
    req = urllib2.Request("http://192.168.22.193")
    opener = urllib2.build_opener()
    f = opener.open(req)
    scans = simplejson.load(f)
    
    stats = {
        'number_of_scans': 0,
        'number_of_new_consumables': 0,
        'number_of_new_consumed': 0,
    }

    for scan in scans:
        stats['number_of_scans'] += 1
        # if Consumable.query.filter_by(upc = scan['upc']).count() == 0:
        #     consumable = Consumable(scan['upc'], look_up_upc(scan['upc']))
        #     db.session.add(consumable)
        #     db.session.commit()
        #     stats['number_of_new_consumables'] += 1
        # consumable = Consumable.query.filter_by(upc = scan['upc']).first()
        #pprint(consumable)
        pprint(stats)
        pprint(scan)
        # if Consumed.query.filter_by(id = scan['id']).count() == 0:
        #     pprint(scan['timestamp'])
        #     timestamp = datetime.strptime(
        #         scan['timestamp']
        #         , '%Y-%m-%dT%H:%M:%S'
        #     )
        #     consumed = Consumed(
        #         id=scan['id']
        #         , datetime=timestamp
        #         , consumable=consumable.id
        #     )
        #     db.session.add(consumed)
        #     db.session.commit()
        #     stats['number_of_new_consumed'] += 1

    pprint(stats)
    return 'Database updated.'

def look_up_upc(upc):
    factual = Factual(
        '1psULPx7BQfmamX3bnkOnR7NWkcPRKcjnSvazvXF'
        , 'Eu8sIGOyXIPrq3jHAudGjkPea4v5v813jJcxOOTW'
    )

    q = factual.table('products-cpg').filters({"upc":upc})
    if q.data():
        result = q.data()[0]
        return "{brand} {product_name}". format(**result)
    return None


@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

