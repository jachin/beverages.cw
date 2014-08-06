#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import urlparse
import simplejson
from pprint import pformat
from datetime import datetime, timedelta
from operator import itemgetter
import ordereddict

import pytz
import yaml

from flask import Flask, request, render_template, jsonify, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from crossdomain import crossdomain

app = Flask(__name__)
app.config.from_pyfile('../beverages.cfg', silent=False)
db = SQLAlchemy(app)

central_tz = pytz.timezone('US/Central')
pi_address = 'http://192.168.22.21/'


class BeverageGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    consumables = db.relationship(
        'Consumable',
        backref='beverage_group',
        lazy='dynamic'
    )

    def __repr__(self):
        return "%s" % self.name


class Consumable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upc = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(120), unique=False)
    consumed = db.relationship(
        'Consumed',
        backref='details',
        lazy='dynamic'
    )
    beverage_group_id = db.Column(
        db.Integer,
        db.ForeignKey('beverage_group.id')
    )

    def __init__(self, upc, name=None, beverage_group_id=beverage_group_id):
        self.upc = upc
        self.name = name
        self.beverage_group_id = beverage_group_id

    def serialize(self):
        return {
            'id': self.id,
            'upc': self.upc,
            'name': self.name,
        }

    def __repr__(self):
        return "%s" % self.name


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


def update_groups_and_consumable():
    stream = open("beverage_data.yaml", 'r')
    beverages_data = yaml.load(stream)

    for (group_name, beverages) in beverages_data.items():
        query = BeverageGroup.query.filter_by(name=group_name)
        if query.count() == 0:
            group = BeverageGroup(name=group_name)
            db.session.add(group)
            db.session.commit()
            app.logger.debug("Adding beverage group: {0}".format(group_name))
        group = BeverageGroup.query.filter_by(name=group_name).first()
        for (beverage_name, upc) in beverages.items():
            query = Consumable.query.filter_by(upc=upc)
            if query.count() == 0:
                consumable = Consumable(
                    upc=upc,
                    name=beverage_name,
                    beverage_group_id=group.id
                )
                db.session.add(consumable)
                db.session.commit()
                app.logger.debug(
                    "Adding a new consumable '{0}' to the beverage group '{1}'".format(
                        beverage_name,
                        group.name
                    )
                )
            consumable = query.first()
            if consumable.beverage_group_id != group.id:
                consumable.beverage_group_id = group.id
                db.session.commit()
                app.logger.debug(
                    "Adding an existing consumable '{0}' to the beverage group '{1}'".format(
                        beverage_name,
                        group.name
                    )
                )
            if consumable.name != beverage_name:
                consumable.name = beverage_name
                db.session.commit()
                app.logger.debug(
                    "Updating the UPC '{0}' with the name '{1}'".format(
                        upc,
                        beverage_name
                    )
                )


def get_bad_upcs():
    stream = open("bad_upcs.yaml", 'r')
    bad_upcs = yaml.load(stream)
    return bad_upcs


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
        app.logger.error("invalid date: {0}".format(datetime_str))

    return dt


def update_url_parameters(url, params):
    url_parts = list(urlparse.urlparse(url))

    url_query = dict(urlparse.parse_qsl(url_parts[4]))
    url_query.update(params)
    url_parts[4] = urllib.urlencode(url_query)

    new_url = urlparse.urlunparse(url_parts)
    return new_url


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stats')
def show_stats():
    scans = []
    for consumed in Consumed.query.all():
        scans.append(consumed.serialize())
    data = {
        'scans': scans
    }
    return render_template('stats.html', **data)


@app.route('/overview')
@app.route('/overview/')
def overview():

    if not request.is_xhr and not request.args.get('json', False):
        return render_template('overview.html')

    start_date = parse_url_date_time(
        request.args.get('start_date', ''),
        start_of_day=True
    )
    end_date = parse_url_date_time(
        request.args.get('end_date', ''),
        start_of_day=False
    )

    query = db.session.query(Consumed)

    if start_date:
        query = query.filter(Consumed.datetime >= start_date)
        start_date_str = start_date.strftime("%Y-%m-%d")
    else:
        start_date_str = ''

    if end_date:
        query = query.filter(Consumed.datetime <= end_date)
        end_date_str = end_date.strftime("%Y-%m-%d")
    else:
        end_date_str = ''

    overview = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'consumed_count': query.count()
    }

    return jsonify(overview=overview)


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

    update_groups_and_consumable()
    bad_upcs = get_bad_upcs()

    last_consumed = Consumed.query.order_by(desc(Consumed.scann_id)).first()

    if last_consumed is None:
        req = urllib2.Request(
            pi_address
        )
    else:
        req = urllib2.Request(
            "{0}after/{1}".format(pi_address, last_consumed.scann_id)
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

        # Look for a consumable with a matching UPC
        query = Consumable.query.filter_by(upc=scan['upc'])

        if query.count() == 0:
            # If we are unable to find one, make a new one with an empty name.
            consumable = Consumable(scan['upc'], name='', beverage_group_id=None)
            db.session.add(consumable)
            db.session.commit()
            stats['number_of_new_consumables'] += 1

        consumable = query.first()

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


# The last 10 scans
@app.route('/scans/')
def scans():
    scans = []
    for consumed in Consumed.query.order_by(Consumed.datetime.desc())[:10]:
        scans.append(consumed.serialize())

    if request.is_xhr and not request.args.get('json', False):
        return jsonify(scans=scans)
    else:
        return render_template('scans.html', scans=scans)


@app.route('/scans/all')
@app.route('/scans/all/')
def show_all():
    json_data = []
    for consumed in Consumed.query.all():
        json_data.append(consumed.serialize())

    return jsonify(drinks=json_data)


@app.route('/drinks')
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

    if request.is_xhr or request.args.get('json', False):
        return jsonify(drinks=drinks)
    else:
        return render_template('drinks.html', drinks=drinks)


@app.route('/drink/<int:consumable_id>/by/day')
@app.route('/drink/<int:consumable_id>/by/day/')
@crossdomain(origin='*')
def show_one_consumable(consumable_id):

    if not request.is_xhr and not request.args.get('json', False):
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

    query = Consumed.query.filter_by(consumable=consumable_id)

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

    # Add empty arrays for the days with no scans.
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


@app.route('/drinks/by/day', methods=['GET'])
@crossdomain(origin='*')
def show_drinks_by_day():

    start_date = parse_url_date_time(
        request.args.get('start_date', ''),
        start_of_day=True
    )
    end_date = parse_url_date_time(
        request.args.get('end_date', ''),
        start_of_day=False
    )

    if start_date is None and end_date is None:
        start_date = datetime.today() - timedelta(weeks=2)
        end_date = datetime.today()

        new_url = update_url_parameters(request.url, {
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
        })
        return redirect(new_url)

    if not request.is_xhr and not request.args.get('json', False):
        return render_template('drinks_by_day.html')

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

    # Add empty arrays for the days with no scans.
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


@app.route('/drinks/by/beverage')
def show_drinks_by_beverage():
    if not request.is_xhr and not request.args.get('json', False):
        return render_template('blank.html')


@app.route('/ping')
@app.route('/ping/')
def ping():

    from pyga.requests import Tracker, Event, Session, Visitor

    upc = request.args.get('upc')

    query = Consumable.query.filter_by(upc=upc)

    consumable = query.first()

    if consumable is not None:
        consumable_name = consumable.name
        group = BeverageGroup.query.filter_by(id=consumable.beverage_group_id).first()
        if group:
            group_name = group.name
        else:
            group_name = 'Unknown'
    else:
        consumable_name = upc
        group_name = 'Unknown'

    tracker = Tracker('UA-5298189-10', 'beverages.cw')

    event_label = "{0}: {1}".format(group_name, consumable_name)

    event = Event('Beverage Fridge', 'Drink', event_label, 1)

    session = Session()
    visitor = Visitor()

    tracker.track_event(event, session, visitor)

    return render_template(
        'ping.html',
        upc=upc,
        name=consumable_name,
        group=group_name
    )


class BeverageGroupModelView(ModelView):
    inline_models = [(Consumable, dict(form_columns=['name']))]

    def __init__(self, session):
        super(BeverageGroupModelView, self).__init__(BeverageGroup, session)

admin = Admin(app, name='Beverage-O-Meter Admin')
admin.add_view(ModelView(Consumable, db.session))
admin.add_view(ModelView(Consumed, db.session))
admin.add_view(BeverageGroupModelView(db.session))

if __name__ == '__main__':
    db.create_all()
    app.debug = True
    app.run(host='0.0.0.0')
