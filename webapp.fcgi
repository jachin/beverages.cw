#!/usr/bin/python
# Standard library
import os
import sys
# Third-party
from flup.server.fcgi import WSGIServer

activate_this = '/www/b/beverages.cw/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# App
from beverages import app

if __name__ == '__main__':
    WSGIServer(app).run()
