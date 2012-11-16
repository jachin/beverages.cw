# all the imports
import urllib, urllib2
import sqlalchemy
from sqlalchemy import *
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Markup

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
    #results = engine.execute('drop table if exists beverage_transaction');
    results = engine.execute('create table if not exists beverage_transaction ( beverage_transaction_id int primary key auto_increment, barcode text not null, transaction_date datetime not null);');
    results = engine.execute('SELECT COUNT(beverage_transaction_id) AS amount, barcode FROM beverage_transaction GROUP BY barcode;');
    out = "<table>"
    for row in results:
        #out += "<li>"+row['barcode']+", "+</li>"
        url = 'http://www.upcdatabase.com/item/'+row['barcode']
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        the_page = response.read()
        the_page = the_page[the_page.index('<td>Description'):];
        out += '<tr><td>Count:</td><td>'+str(row['amount'])+'</td>'+the_page[:the_page.index('</tr>')]+'</tr>';
    
    results.close()
    out += "</table>"
#    return the_page[:the_page.index('</tr>')];
    return Markup(out)
#    return render_template('hi.html', message='message text')

if __name__ == '__main__':
    app.run(host='0.0.0.0')


