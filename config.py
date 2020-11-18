import logging
from datetime import timedelta
from redis import StrictRedis


class Config(object):

    DEBUG = True
    SECRET_KEY = "hlfdsjglfdsjgl"

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:123456@localhost:3306/info3"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    SESSION_TYPE = "redis"
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=2)
    LEVEL_NAME = logging.DEBUG


class DevelopConfig(Config):
    pass


class ProductConfig(Config):
    DEBUG = False
    LEVEL_NAME = logging.ERROR


class TestConfig(Config):
    pass


class DevelopmentConfig(Config):
    pass


config_dict = {
    "develop": DevelopConfig,
    "product": ProductConfig,
    "test": TestConfig

}