# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from operator import itemgetter
import ordereddict
import simplejson
import pytz

from crossdomain import crossdomain

from flask import request, render_template, jsonify, redirect

from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from beverages import app, central_tz
from util import update_locations, update_groups_and_consumable, update_bom
from util import parse_url_date_time, update_url_parameters

from models import db, ScannerLocation
from models import BeverageGroup, Consumable, Consumed

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/update_db')
@app.route('/update_db/')
def update_database():

    update_locations()
    update_groups_and_consumable()

    for location in ScannerLocation.query.all():
        stats = update_bom(location)

    return render_template('update_database.html', **stats)


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


# The last 10 scans
@app.route('/scans/last-10')
@app.route('/scans/last-10/')
def scans():
    scans = []
    for consumed in Consumed.query.order_by(Consumed.datetime.desc())[:10]:
        scans.append(consumed.serialize())

    if request.is_xhr and not request.args.get('json', False):
        return jsonify(scans=scans)
    else:
        return render_template('scans_last_10.html', scans=scans)


@app.route('/scans/all')
@app.route('/scans/all/')
def show_all():

    if not request.is_xhr and not request.args.get('json', False):
        return render_template('blank.html')

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


@app.route('/graph/beverages/by/time')
@app.route('/graph/beverages/by/time/')
def graph_beverages_by_time():
    query = db.session.query(Consumed)
    query.order_by(Consumed.datetime)

    drinks_by_hour = {}

    for consumed in query.all():
        datetime_gmt = consumed.datetime.replace(tzinfo=pytz.utc)
        datetime_cst = datetime_gmt.astimezone(central_tz)

        hour = datetime_cst.strftime("%H")

        hour = int(hour);

        if hour not in drinks_by_hour:
            drinks_by_hour[hour] = {
                'hour': hour,
                'number': 0
            }

        drinks_by_hour[hour]['number'] += 1

    for hour in range(24):
        if hour not in drinks_by_hour:
            drinks_by_hour[hour] = {
                'hour': hour,
                'number': 0
            }

    drinks_by_hour = sorted(drinks_by_hour.values(), key=itemgetter('hour'))

    data = {
        'drinks_by_hour': simplejson.dumps(drinks_by_hour)
    }

    return render_template('graph_beverages_by_time.html', **data)


@app.route('/year/summary')
def year_summary():
    query = db.session.query(Consumed)
    query.order_by(Consumed.datetime)

    drinks_by_years = {}

    for consumed in query.all():
        datetime_gmt = consumed.datetime.replace(tzinfo=pytz.utc)
        datetime_cst = datetime_gmt.astimezone(central_tz)

        year = datetime_cst.strftime("%Y")

        year = int(year);

        if year not in drinks_by_years:
            drinks_by_years[year] = {
                'year': year,
                'number': 0,
                'drinks': {},
            }

        drinks_by_years[year]['number'] += 1


    drinks_by_years = ordereddict.OrderedDict(sorted(drinks_by_years.items()))

    data = {
        'drinks_by_years': drinks_by_years.values()
    }

    return render_template('year_summary.html', **data)


class BeverageGroupModelView(ModelView):
    inline_models = [(Consumable, dict(form_columns=['name']))]

    def __init__(self, session):
        super(BeverageGroupModelView, self).__init__(BeverageGroup, session)

class ConsumableGroupModelView(ModelView):

    def __init__(self, session):
        super(ConsumableGroupModelView, self).__init__(Consumable, session)


admin = Admin(app, name='Beverage-O-Meter Admin')
admin.add_view(ConsumableGroupModelView(db.session))
admin.add_view(ModelView(Consumed, db.session))
admin.add_view(BeverageGroupModelView(db.session))
