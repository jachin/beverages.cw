#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import simplejson
from pprint import pprint
from datetime import datetime, timedelta
from operator import itemgetter
import logging
import ordereddict

import pytz

from flask import Flask, request, render_template, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqlamodel import ModelView

app = Flask(__name__)
app.config.from_pyfile('../beverages.cfg', silent=False)
db = SQLAlchemy(app)

central_tz = pytz.timezone('US/Central')

# The following are bar codes that are not really beverages. Most of them got
#   there for testing.
bad_upcs = [
    '01630165745',
    '03758800824',
    '0491347',
    '0491347',
    '0728510322',
    '0733607411',
    '0733607411',
    '073867351',
    '073867351',
    '0820016575',
    '0820016575',
    '0832123609',
    '0832123609',
    '08432500187'
    '088110105',
    '088110105',
    '088749344',
    '088749344',
    '09998807196',
    '09998807196',
    '4205541228',
    '5315',
    '854290048',
    '854290048',
    '978032134693',
    '97805652010',
    '978136594313',
    '978156592470',
]


known_upcs = {
    '012303': 'Pepsi',
    '05100187291': 'V8 V-Fusion (Strawberry Banana)',
    '0510018737': 'V8 V-Fusion (Pomegrannate Blueberry)',
    '07831504': 'Dr Pepper',
    '6112690173': 'Red Bull - Sugar Free',
    '611269991000': 'Red Bull',
    '784811169':  'Monster',
    '784811268': 'Monster Low Cal',
    '049504': 'Cherry Coke-a-Cola',
    '012660': 'Diet Mnt Dew',
    '012508': 'Diet Pepsi',
    '794522200788': 'Tazo Awake Black Tea (Box of 20)',
    '04900004632': 'Coke-a-Cola (MX)',
}


class Consumable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upc = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(120), unique=False)
    consumed = db.relationship(
        'Consumed',
        backref='details',
        lazy='dynamic'
    )

    def __init__(self, upc, name=None):
        self.upc = upc
        self.name = name

    def serialize(self):
        return {
            'id': self.id,
            'upc': self.upc,
            'name': self.name,
        }

    def __repr__(self):
        return '<Consumable %r>' % (self.name)


class Consumed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scann_id = db.Column(db.Integer, unique=True, index=True)
    datetime = db.Column(db.DateTime())
    consumable = db.Column(
        'consumable_id',
        db.Integer,
        db.ForeignKey("consumable.id"),
        nullable=False
    )

    def serialize(self):

        scan_datetime = self.datetime.replace(tzinfo=pytz.utc)

        scan_datetime_cst = scan_datetime.astimezone(central_tz)

        return {
            'id': self.id,
            'scann_id': self.scann_id,
            'datetime': scan_datetime.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
            'datetime_gmt_human': scan_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            'datetime_cst': scan_datetime_cst.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
            'datetime_cst_human': scan_datetime_cst.strftime("%Y-%m-%d %H:%M:%S"),
            'type_id': self.details.id,
            'upc': self.details.upc,
            'name': self.details.name,
        }

    def __repr__(self):
        return '<Consumed %r>' % (self.id)


def look_up_upc(upc):
    if upc in known_upcs:
        return known_upcs[upc]
    return None


def parse_url_date_time(datetime_str, start_of_day=True):

    dt = None

    try:
        dt = datetime.strptime(datetime_str, '%Y-%m-%d  %H:%M:%S')
        return dt
    except ValueError:
        pass

    try:
        dt = datetime.strptime(datetime_str, '%Y-%m-%d')
        if start_of_day:
            dt = dt.replace(hour=0, minute=0, second=0)
        else:
            dt = dt.replace(hour=23, minute=59, second=59)
    except ValueError:
        logging.error("invalid date: {0}".format(datetime_str))

    return dt


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

    return simplejson.dumps(data)


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


@app.route('/demo/')
def demo():
    return render_template('demo.html')


@app.route('/update_db')
@app.route('/update_db/')
def update_database():

    last_consumed = Consumed.query.order_by(desc(Consumed.scann_id)).first()

    if last_consumed is None:
        req = urllib2.Request(
            "http://192.168.22.193/"
        )
    else:
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

        if scan['upc'] in bad_upcs:
            # skip any bad upcs
            continue

        query = Consumable.query.filter_by(upc=scan['upc'])
        if query.count() == 0:
            name = look_up_upc(scan['upc'])

            consumable = Consumable(scan['upc'], name)
            db.session.add(consumable)
            db.session.commit()
            stats['number_of_new_consumables'] += 1
        consumable = Consumable.query.filter_by(upc=scan['upc']).first()
        if Consumed.query.filter_by(scann_id=scan['id']).count() == 0:

            timestamp = datetime.strptime(
                scan['timestamp'],
                '%Y-%m-%dT%H:%M:%S'
            )

            timestamp = timestamp.replace(tzinfo=pytz.utc)

            consumed = Consumed(
                scann_id=scan['id'],
                datetime=timestamp,
                consumable=consumable.id
            )
            db.session.add(consumed)
            db.session.commit()
            stats['number_of_new_consumed'] += 1

    return render_template('update_database.html', **stats)


@app.route('/update_consumable/')
def update_consumable():
    for consumable in Consumable.query.filter_by(name=None):
        name = look_up_upc(consumable.upc)
        if name:
            consumable.name = name
            db.session.commit()

    stats = {}
    return render_template('update_consumable_name.html', **stats)


@app.route('/scans/')
def scans():
    scans = []
    for consumed in Consumed.query.order_by(Consumed.datetime.desc())[:10]:
        scans.append(consumed.serialize())

    if request.is_xhr:
        return jsonify(scans=scans)
    else:
        return render_template('scans.html', scans=scans)


@app.route('/all/')
def show_all():
    json_data = []
    for consumed in Consumed.query.all():
        json_data.append(consumed.serialize())

    return simplejson.dumps(json_data)


@app.route('/drinks/')
def show_consumables():

    drinks = []
    for consumable in Consumable.query.all():

        drink_data = consumable.serialize()
        total_number = Consumed.query.filter_by(consumable=consumable.id).count()
        drink_data['total_number'] = total_number
        drinks.append(drink_data)

    # Sort by the total number of drinks
    drinks = sorted(drinks, key=itemgetter('total_number'), reverse=True)

    if request.is_xhr:
        return jsonify(drinks=drinks)
    else:
        return render_template('drinks.html', drinks=drinks)


@app.route('/drink/<int:consumable_id>/by/day')
@app.route('/drink/<int:consumable_id>/by/day/')
def show_one_consumable(consumable_id):

    if not request.is_xhr:
        return render_template('drink_by_day.html')

    start_date = parse_url_date_time(
        request.args.get('start_date', ''),
        start_of_day=True
    )
    end_date = parse_url_date_time(
        request.args.get('end_date', ''),
        start_of_day=False
    )

    data = {}

    query = Consumed.query.filter_by(consumed=consumable_id)

    query.order_by(Consumed.datetime)

    if start_date:
        query = query.filter(Consumed.datetime >= start_date)

    if end_date:
        query = query.filter(Consumed.datetime <= end_date)

    for consumed in query.all():

        datetime_gmt = consumed.datetime.replace(tzinfo=pytz.utc)
        datetime_cst = datetime_gmt.astimezone(central_tz)

        day_str = datetime_cst.strftime("%Y-%m-%d")

        if day_str in data:
            data[day_str].append(consumed.serialize())
        else:
            data[day_str] = [consumed.serialize(), ]

    pprint(data)

    # Add empty ararys for the days with no scans.
    previous_day = None
    one_day = timedelta(days=1)
    for day, scans in sorted(data.items()):
        if previous_day is None:
            previous_day = parse_url_date_time(day)
        else:
            current_day = previous_day + one_day
            day = parse_url_date_time(day)
            while current_day < day:
                current_day_str = current_day.strftime("%Y-%m-%d")
                data[current_day_str] = []
                current_day = current_day + one_day
            previous_day = current_day

    data = ordereddict.OrderedDict(sorted(data.items()))

    return jsonify(drink_by_day=data.items())


@app.route('/drinks/by/day')
def show_drinks_by_day():

    if not request.is_xhr:
        return render_template('drinks_by_day.html')

    start_date = parse_url_date_time(
        request.args.get('start_date', ''),
        start_of_day=True
    )
    end_date = parse_url_date_time(
        request.args.get('end_date', ''),
        start_of_day=False
    )

    data = {}

    query = db.session.query(Consumed)

    query.order_by(Consumed.datetime)

    if start_date:
        query = query.filter(Consumed.datetime >= start_date)

    if end_date:
        query = query.filter(Consumed.datetime <= end_date)

    for consumed in query.all():

        datetime_gmt = consumed.datetime.replace(tzinfo=pytz.utc)
        datetime_cst = datetime_gmt.astimezone(central_tz)

        day_str = datetime_cst.strftime("%Y-%m-%d")

        if day_str in data:
            data[day_str].append(consumed.serialize())
        else:
            data[day_str] = [consumed.serialize(), ]

    # Add empty ararys for the days with no scans.
    previous_day = None
    one_day = timedelta(days=1)
    for day, scans in sorted(data.items()):
        if previous_day is None:
            previous_day = parse_url_date_time(day)
        else:
            current_day = previous_day + one_day
            day = parse_url_date_time(day)
            while current_day < day:
                current_day_str = current_day.strftime("%Y-%m-%d")
                data[current_day_str] = []
                current_day = current_day + one_day
            previous_day = current_day

    data = ordereddict.OrderedDict(sorted(data.items()))

    return jsonify(drinks_by_day=data.items())


admin = Admin(app, name='Beverage-O-Meter Admin')
admin.add_view(ModelView(Consumable, db.session))
admin.add_view(ModelView(Consumed, db.session))

if __name__ == '__main__':
    db.create_all()
    app.debug = True
    app.run(host='0.0.0.0')
