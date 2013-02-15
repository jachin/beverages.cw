from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('../beverages.cfg', silent=False)
db = SQLAlchemy(app)

class Consumable(db.Model):
    __tablename__ = 'consumable'
    id = db.Column(db.Integer, primary_key=True)
    upc = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(120), unique=False)

    def __init__(self, upc, name):
        self.upc = upc
        self.name= name

    def __repr__(self):
        return '<Consumable %r>' % (self.name)


class Consumed(db.Model):
    __tablename__ = 'consumed'
    id = db.Column(db.Integer, primary_key=True)
    scann_id = db.Column(db. Integer)
    datetime = db.Column(db.DateTime())
    consumable = db.Column(
        'consumable_id'
        , db.Integer
        , db.ForeignKey("consumable.id")
        , nullable=False
    )

    def __repr__(self):
        return '<Consumed %r>' % (self.id)