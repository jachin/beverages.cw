# -*- coding: utf-8 -*-


from flask.ext.admin.contrib.sqla import ModelView

from beverages import app, db

from beverages.beverage_stats.models import BeverageGroup, Consumable, Consumed


class BeverageGroupModelView(ModelView):
    inline_models = [(Consumable, dict(form_columns=['name']))]

    def __init__(self, session):
        super(BeverageGroupModelView, self).__init__(BeverageGroup, session)

class ConsumableGroupModelView(ModelView):

    def __init__(self, session):
        super(ConsumableGroupModelView, self).__init__(Consumable, session)

