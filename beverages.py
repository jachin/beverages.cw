import urllib2
import simplejson
from pprint import pprint

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from flask import Flask, request, session, url_for, render_template, flash

from contextlib import closing

# create our little application :)
app = Flask(__name__)
#app.config.from_object(settings.DevelopmentConfig)
app.config.from_pyfile('../etc/beverages.cfg', silent=False)

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)

db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    import models
    Base.metadata.create_all(bind=engine)

@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def show_stats():
    return 'Beverage-o-meter'


@app.route('/update_db/')
def update_database():
    req = urllib2.Request("http://192.168.22.193")
    opener = urllib2.build_opener()
    f = opener.open(req)
    scans = simplejson.load(f)
    
    for scan in scans:
        if is_new_consumable(scan['upc']):
            add_new_consumable(scan['upc'])
        if is_new_consumed(scan['id']):
            add_new_consumed(scan['id'],scan['timestamp'],scan['upc'])

    return 'Database updated.'

def hi( ):
    #results = engine.execute('INSERT INTO beverage_transaction (barcode, transaction_date) VALUES(SHA1(NOW()), NOW() );');
    results = engine.execute('SELECT COUNT(consumed.id) AS amount, consumable.upc, consumable.name FROM consumed, consumable WHERE consumable.id=consumed.consumable_id GROUP BY name;');
    out = '<html><head><script type="text/javascript" src="../src/plugins/jqplot.pieRenderer.min.js"></script><script type="text/javascript" src="../src/plugins/jqplot.donutRenderer.min.js"></script></head><body><table>'
    for row in results:
        url = 'http://www.upcdatabase.com/item/'+row['upc']
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        the_page = response.read()
        the_page = the_page[the_page.index('<td>Description'):];
        out += '<tr><td>Count:</td><td>'+str(row['amount'])+'</td>'+the_page[:the_page.index('</tr>')]+'</tr>';
    
    results.close()
    out += "</table></body></html>"
#    return the_page[:the_page.index('</tr>')];
    return Markup(out)
#    return render_template('hi.html', message='message text')

if __name__ == '__main__':
    app.run(debug=True)

