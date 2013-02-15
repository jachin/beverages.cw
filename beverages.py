import urllib2
import simplejson
from pprint import pprint
from datetime import datetime

from factual import Factual

from flask import Flask, request, session, url_for, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_, desc
from sqlalchemy.ext.serializer import loads, dumps
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView


from contextlib import closing

app = Flask(__name__)
app.config.from_pyfile('../beverages.cfg', silent=False)
db = SQLAlchemy(app)

class Consumable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upc = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(120), unique=False)
    consumed = db.relationship(
        'Consumed',
        backref='details',
        lazy='dynamic'
    )

    def __init__(self, upc, name):
        self.upc = upc
        self.name= name

    def __repr__(self):
        return '<Consumable %r>' % (self.name)
    
    def serialize(self):
        return {
            'id': self.id,
            'upc': self.upc,
            'name': self.name,
        }


class Consumed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scann_id = db.Column(db.Integer, unique=True, index=True)
    datetime = db.Column(db.DateTime())
    consumable = db.Column(
        'consumable_id'
        , db.Integer
        , db.ForeignKey("consumable.id")
        , nullable=False
    )

    def serialize(self):
        return {
            'id': self.id,
            'scann_id': self.scann_id,
            'datetime': self.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            'upc': self.details.upc,
            'name': self.details.name,
        }

    def __repr__(self):
        return '<Consumed %r>' % (self.id)


@app.route('/')
def show_stats():
    scans = []
    for consumed in Consumed.query.all():
        #pprint(consumed)
        scans.append(consumed.serialize())
    data = {
        'scans': scans
    }
    return render_template('stats.html', **data)

@app.route('/days/<day_string>')
def days(day_string):
    days = {}
    for consumed in Consumed.query.all():

        if day_string in ['group-by-day']:
            date_string = consumed.datetime.strftime("%a")
        else:
            date_string = consumed.datetime.strftime("%Y-%m-%d")

        if date_string not in days.keys():
            days[date_string] = []
            
        days[date_string].append(consumed.serialize())

    data = {
        'days': days
    }

    return simplejson.dumps( days )
    
@app.route('/graph')
def graph():

    hours = {}
    drinks = {}
    
    for consumable in Consumable.query.all():
        consumable = consumable.serialize()
        drinks[consumable['upc']] = {'id': consumable['id'], 'name': consumable['name']}

    for consumed in Consumed.query.all():

        hour = consumed.datetime.strftime("%H")
        consumed = consumed.serialize()

        if hour not in hours.keys():
            hours[hour] = {}
            
        if consumed['upc'] not in hours[hour].keys():
            hours[hour][consumed['upc']] = 0

        hours[hour][consumed['upc']] += 1

    data = {
        'drinks': simplejson.dumps(drinks),
        'hours': simplejson.dumps(hours)
    }

    return render_template('graph.html', **data)


@app.route('/update_db/')
def update_database():

    last_consumed = Consumed.query.order_by(desc(Consumed.scann_id)).first()

    req = urllib2.Request(
        "http://192.168.22.193/after/{0}".format(last_consumed.scann_id)
    )
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
        if Consumable.query.filter_by(upc = scan['upc']).count() == 0:
            consumable = Consumable(scan['upc'], look_up_upc(scan['upc']))
            db.session.add(consumable)
            db.session.commit()
            stats['number_of_new_consumables'] += 1
        consumable = Consumable.query.filter_by(upc = scan['upc']).first()
        if Consumed.query.filter_by(scann_id = scan['id']).count() == 0:
            timestamp = datetime.strptime(
                scan['timestamp']
                , '%Y-%m-%dT%H:%M:%S'
            )
            consumed = Consumed(
                scann_id=scan['id']
                , datetime=timestamp
                , consumable=consumable.id
            )
            db.session.add(consumed)
            db.session.commit()
            stats['number_of_new_consumed'] += 1

    return render_template('update_database.html', **stats)


@app.route('/all/')
def show_all():
    #return simplejson.dumps( Consumed.query.all() )
    json_data = []
    for consumed in Consumed.query.all():
        #pprint(consumed)
        json_data.append(consumed.serialize())

    #pprint(json_data)

    # for consumed in Consumed.query.join(Consumable).all():
    #     pprint(consumed)
    #     pprint(consumed.item)
        

    return simplejson.dumps( json_data )


def look_up_upc(upc, force_external_lookup=False):
    # use database
    consumeable = Consumable.query.filter_by(upc=upc).first()
    if (consumeable != None):
        return consumeable.name

    # use eandata.com
    api_key = 'E37966CA511E8E1C'
    url = 'http://eandata.com/feed.php'
    mode = 'json'
    method = 'find'
    result = urllib2.urlopen(url + '?keycode=' + api_key + '&mode=' + mode + '&' + method + '=' + upc).read()
    result = simplejson.loads(str(result))
    if (result['product']['product']):
        return result['product']['product']
        
    # use factual
    factual = Factual(
        '1psULPx7BQfmamX3bnkOnR7NWkcPRKcjnSvazvXF'
        , 'Eu8sIGOyXIPrq3jHAudGjkPea4v5v813jJcxOOTW'
    )

    q = factual.table('products-cpg').filters({"upc":upc})
    if q.data():
        result = q.data()[0]
        return "{brand} {product_name}". format(**result)

    return None

@app.route('/lookup/<upc>')
def look_up_test(upc):
    return look_up_upc(upc)

@app.route('/lookup-and-save/<upc>')
def lookup_and_save(upc):

    name = look_up_upc(upc, True)
    consumable = Consumable.query.filter_by(upc=upc).first()
    
    if (consumable == None):
        consumable = Consumable(upc, name)
        db.session.add(consumable)
    
    else:
        consumable.name = name
    
    db.session.commit()
    
    consumable = Consumable.query.filter_by(upc=upc).first()
    return str(consumable)

admin = Admin(app, name='Beverage-O-Meter Admin')
admin.add_view(ModelView(Consumable, db.session))
admin.add_view(ModelView(Consumed, db.session))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

