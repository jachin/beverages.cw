# vim: ft=python:
import os
import sys

activate_this = '/www/b/beverages.cw/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from beverages import app as application
