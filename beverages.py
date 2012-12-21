import urllib2
import simplejson
from pprint import pprint
from datetime import datetime

from pyquery import PyQuery

from flask import Flask, request, session, url_for, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy

from contextlib import closing

app = Flask(__name__)
app.config.from_pyfile('../beverages.cfg', silent=False)
db = SQLAlchemy(app)

class Consumable(db.Model):
    __tablename__ = 'consumable'
    id = db.Column(db.Integer, primary_key=True)
    upc = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(120), unique=True)

    def __init__(self, upc, name):
        self.upc = upc
        self.name= name

    def __repr__(self):
        return '<Consumable %r>' % (self.name)


class Consumed(db.Model):
    __tablename__ = 'consumed'
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime())
    consumable = db.Column(
        'consumable_id'
        , db.Integer
        , db.ForeignKey("consumable.id")
        , nullable=False
    )

    def __repr__(self):
        return '<Consumed %r>' % (self.id)


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
        if Consumable.query.filter_by(upc = scan['upc']).count() == 0:
            consumable = Consumable(scan['upc'], look_up_upc(scan['upc']))
            db.session.add(consumable)
            db.session.commit()
        consumable = Consumable.query.filter_by(upc = scan['upc']).first()
        pprint(consumable)
        if Consumed.query.filter_by(id = scan['id']).count() == 0:
            pprint(scan['timestamp'])
            timestamp = datetime.strptime(
                scan['timestamp']
                , '%Y-%m-%dT%H:%M:%S'
            )
            consumed = Consumed(
                id=scan['id']
                , datetime=timestamp
                , consumable=consumable.id
            )
            db.session.add(consumed)
            db.session.commit()

    return 'Database updated.'

def look_up_upc(upc):
    url = 'http://www.upcdatabase.com/item/'+upc
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    page = PyQuery(response.read())

    for label_row in page.find('table.data tr td:first-child'):
        label_row = PyQuery(label_row)
        if label_row.text() == "Description":
            description_cell = label_row.siblings()[-1]
            return description_cell.text



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
    app.run(host='0.0.0.0')

