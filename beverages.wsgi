activate_this = '/www/b/beverages.cw/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
from beverages import app as application
