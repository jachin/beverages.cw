#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytz

from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('../beverages.cfg', silent=False)

central_tz = pytz.timezone('US/Central')
ip_address = 'http://192.168.22.211/'

import views

if __name__ == '__main__':

    app.debug = True

    app.run(host='0.0.0.0')
