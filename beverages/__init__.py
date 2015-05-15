# -*- coding: utf-8 -*-

import pytz

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin

app = Flask(__name__)
app.config.from_pyfile('../../beverages.cfg', silent=False)

app.logger.debug(app.config['SQLALCHEMY_DATABASE_URI'])

db = SQLAlchemy(app)
tz = pytz.timezone(app.config['TIMEZONE'])

from models import Consumable, Consumed, Barcode
from models import ScannerLocation, BeverageGroup

from beverages.bower import mod as bowerModules
from beverages.beverage_stats.views import mod as beverageStatsModule

app.register_blueprint(bowerModules, url_prefix='/bower')
app.register_blueprint(beverageStatsModule, url_prefix='/')

#from admin import ConsumableGroupModelView, BeverageGroupModelView

#admin = Admin(app, name='Beverage-O-Meter Admin')
#admin.add_view(ConsumableGroupModelView(db.session))
#admin.add_view(ModelView(Consumed, db.session))
#admin.add_view(BeverageGroupModelView(db.session))
