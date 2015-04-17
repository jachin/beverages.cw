# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from operator import itemgetter
import ordereddict
import simplejson
import pytz

from crossdomain import crossdomain

from flask import request, render_template, jsonify, redirect



from beverages import app, central_tz
from util import update_locations, update_groups_and_consumable, update_bom
from util import parse_url_date_time, update_url_parameters



@app.route('/')
def index():
    return render_template('index.html')






