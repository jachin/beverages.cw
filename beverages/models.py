# -*- coding: utf-8 -*-

import pytz

from beverages import tz, db

class ScannerLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50), unique=True)

    def __init__(self, address, name):
        self.address = address
        self.name = name

    def __repr__(self):
        return "<ScannerLocation {0}>".format(self.name)


class BeverageGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    consumables = db.relationship(
        'Consumable',
        backref='beverage_group',
        lazy='dynamic'
    )

    def __repr__(self):
        return "%s" % self.name


class Consumable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=False)
    beverage_group_id = db.Column(
        db.Integer,
        db.ForeignKey('beverage_group.id')
    )
    barcodes = db.relationship(
        'Barcode',
        backref='barcodes',
        lazy='dynamic'
    )

    def __init__(self, name=None, beverage_group_id=beverage_group_id):
        self.name = name
        self.beverage_group_id = beverage_group_id

    def serialize(self):
        return {
            'id': self.id,
            'upc': self.barcodes,
            'name': self.name,
        }

    def __repr__(self):
        return "%s" % self.name

    @staticmethod
    def get_or_create_by_barcode(upc):
        query = Barcode.query.filter_by(upc=upc)
        if query.count() == 0:

            consumable = Consumable(name='', beverage_group_id=None)
            db.session.add(consumable)
            db.session.commit()

            barcode = Barcode(
                upc=upc,
                consumable_id=consumable.id,
            )
            db.session.add(barcode)
            db.session.commit()
        barcode = Barcode.query.filter_by(upc=upc).first()
        return Consumable.query.get(barcode.consumable_id)


class Consumed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(50), unique=True, index=True)
    datetime = db.Column(db.DateTime())
    location = db.Column(
        'scanner_location_id',
        db.Integer,
        db.ForeignKey("scanner_location.id"),
        nullable=False
    )
    barcode_id = db.Column(
        'barcode_id',
        db.Integer,
        db.ForeignKey("barcode.id"),
        nullable=False
    )

    barcode = db.relationship(
        'Barcode',
        backref='barcode_id',
    )

    def serialize(self):

        scan_datetime = self.datetime.replace(tzinfo=pytz.utc)

        scan_datetime_cst = scan_datetime.astimezone(tz)

        return {
            'id': self.id,
            'uuid': self.uuid,
            'datetime': scan_datetime.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
            'datetime_gmt_human': scan_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            'datetime_cst': scan_datetime_cst.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
            'datetime_cst_human': scan_datetime_cst.strftime("%Y-%m-%d %H:%M:%S"),
            'type_id': self.barcode.id,
            'upc': self.barcode.upc,
            'name': self.barcode.consumable.name,
        }

    def __repr__(self):
        return '<Consumed %r>' % (self.id)


class Barcode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consumable_id = db.Column(
        db.Integer,
        db.ForeignKey("consumable.id"),
        nullable=False
    )
    upc = db.Column(db.String(50), unique=True)

    consumable = db.relationship(
        'Consumable',
        backref='consumable_id',
    )

    def __init__(self, consumable_id=consumable_id, upc=upc):
        self.consumable_id = consumable_id
        self.upc = upc
