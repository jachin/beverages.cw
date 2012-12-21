from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from beverages import Base


class Consumable(Base):
    __tablename__ = 'consumable'
    id = Column(Integer, primary_key=True)
    upc = Column(String(50), unique=True)
    name = Column(String(120), unique=True)

    def __init__(self, upc, name):
        self.upc = upc
        self.name= name

    def __repr__(self):
        return '<Consumable %r>' % (self.name)


class Consumed(Base):
    __tablename__ = 'consumed'
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime())
    name = Column(
        'consumable_id'
        , Integer
        , ForeignKey("consumable.id")
        , nullable=False
    )

    def __repr__(self):
        return '<Consumed %r>' % (self.id)