# all the imports
import urllib, urllib2
import sqlalchemy
from sqlalchemy import *
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Markup, url_for

# configuration
DATABASE = 'beverages_cw'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'beverages_cw'
PASSWORD = 'SwovRenPanOnpeir'

# get database setup
engine = create_engine('mysql://'+USERNAME+':'+PASSWORD+'@localhost/'+DATABASE+'?charset=utf8&use_unicode=0',pool_recycle=3600)

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

@app.route('/')
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


