# configuration
DATABASE = 'beverages_cw'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'beverages_cw'
PASSWORD = 'SwovRenPanOnpeir'


class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://:memory:'


class ProductionConfig(Config):
    
    database_username = 'beverages_cw'
    database_password = 'SwovRenPanOnpeir'
    database_name = 'beverages_cw'

    DEBUG = True
    SECRET_KEY = 'development key'
    SQLALCHEMY_DATABASE_URI = 'mysql://{0}:{1}@localhost/{2}'.format(
        database_name, database_password, database_name
    )

    SQLALCHEMY_DATABASE_URI = 'mysql://beverages_cw:SwovRenPanOnpeir@localhost/beverages_cw'


class DevelopmentConfig(Config):
    DATABASE = 'beverages.db'
    DEBUG = True
    SECRET_KEY = 'development key'
    USERNAME = 'admin'
    PASSWORD = 'default'
    DATABASE_URI = 'sqlite://beverages.db'


class TestingConfig(Config):
    TESTING = True