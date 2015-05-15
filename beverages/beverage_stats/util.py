# -*- coding: utf-8 -*-

import urllib2
import urllib
import urlparse
from datetime import datetime

import yaml
from sqlalchemy import desc
import simplejson
import pytz

from beverages import app

from beverages.models import db, ScannerLocation
from beverages.models import BeverageGroup, Consumable, Consumed, Barcode

def update_locations():

    stream = open("locations.yaml", 'r')
    location_data = yaml.load(stream)

    for (title, location_data) in location_data.items():
        name = location_data['Name']
        address = location_data['Address']
        if ScannerLocation.query.filter_by(name=name).count() == 0:
            location = ScannerLocation(name=name, address=address)
            db.session.add(location)
            db.session.commit()
        #TODO Update and Delete Locations
        location = ScannerLocation.query.filter_by(name=name).first()


def update_groups_and_consumable():

    stream = open("beverage_data.yaml", 'r')
    beverages_data = yaml.load(stream)

    for (group_name, beverages) in beverages_data.items():
        query = BeverageGroup.query.filter_by(name=group_name)
        if query.count() == 0:
            group = BeverageGroup(name=group_name)
            db.session.add(group)
            db.session.commit()
            app.logger.debug("Adding beverage group: {0}".format(group_name))
        group = BeverageGroup.query.filter_by(name=group_name).first()
        for (beverage_name, upc) in beverages.items():

            if Consumable.query.filter_by(name=beverage_name).count() == 0:
                consumable = Consumable(
                    name=beverage_name,
                    beverage_group_id=group.id
                )
                db.session.add(consumable)
                db.session.commit()
                app.logger.debug("Adding consumable: {0}".format(beverage_name))

            consumable = Consumable.query.filter_by(name=beverage_name).first()

            if Barcode.query.filter_by(upc=upc).count() == 0:
                barcode = Barcode(
                    upc=upc,
                    consumable_id=consumable.id,
                )
                db.session.add(barcode)
                db.session.commit()
                app.logger.debug(
                    "Adding a new bar code '{0}' to the consumable '{1}'".format(
                        upc,
                        beverage_name
                    )
                )

            if consumable.beverage_group_id != group.id:
                consumable.beverage_group_id = group.id
                db.session.commit()
                app.logger.debug(
                    "Adding an existing consumable '{0}' to the beverage group '{1}'".format(
                        beverage_name,
                        group.name
                    )
                )
            if consumable.name != beverage_name:
                consumable.name = beverage_name
                db.session.commit()
                app.logger.debug(
                    "Updating the UPC '{0}' with the name '{1}'".format(
                        upc,
                        beverage_name
                    )
                )


def update_bom(location):

    bad_upcs = get_bad_upcs()

    last_consumed = Consumed.query.filter_by(
        location=location.id
    ).order_by(
        desc(Consumed.datetime)
    ).first()

    url = "http://{0}".format(location.address)

    if last_consumed is None:
        req = urllib2.Request(url)
    else:
        req = urllib2.Request("{0}/after/{1}".format(url, last_consumed.uuid))

    opener = urllib2.build_opener()
    f = opener.open(req)
    scans = simplejson.load(f)

    stats = {
        'number_of_scans': 0,
        'number_of_new_consumables': 0,
        'number_of_new_consumed': 0,
    }

    for scan in scans:
        stats['number_of_scans'] += 1

        if scan['upc'] in bad_upcs:
            # skip any bad upcs
            continue

        consumable = Consumable.get_or_create_by_barcode(scan['upc'])
        barcode = Barcode.query.filter_by(upc=scan['upc']).first()

        if consumable.name == '':
            stats['number_of_new_consumables'] += 1

        if Consumed.query.filter_by(uuid=scan['uuid']).count() == 0:
            timestamp = datetime.strptime(
                scan['timestamp'],
                '%Y-%m-%dT%H:%M:%S'
            )

            timestamp = timestamp.replace(tzinfo=pytz.utc)

            consumed = Consumed(
                uuid=scan['uuid'],
                datetime=timestamp,
                barcode=barcode.id,
                location=location.id
            )
            db.session.add(consumed)
            db.session.commit()
            stats['number_of_new_consumed'] += 1

    return stats


def get_bad_upcs():
    stream = open("bad_upcs.yaml", 'r')
    bad_upcs = yaml.load(stream)
    return bad_upcs


def parse_url_date_time(datetime_str, start_of_day=True):

    dt = None

    try:
        dt = datetime.strptime(datetime_str, '%Y-%m-%d  %H:%M:%S')
        return dt
    except ValueError:
        pass

    try:
        dt = datetime.strptime(datetime_str, '%Y-%m-%d')
        if start_of_day:
            dt = dt.replace(hour=0, minute=0, second=0)
        else:
            dt = dt.replace(hour=23, minute=59, second=59)
    except ValueError:
        app.logger.error("invalid date: {0}".format(datetime_str))

    return dt


def update_url_parameters(url, params):
    url_parts = list(urlparse.urlparse(url))

    url_query = dict(urlparse.parse_qsl(url_parts[4]))
    url_query.update(params)
    url_parts[4] = urllib.urlencode(url_query)

    new_url = urlparse.urlunparse(url_parts)
    return new_url


