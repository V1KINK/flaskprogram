import logging
from redis import StrictRedis


class Config(object):
    DEBUG = True

    SECRET_KEY = "KrVXEGfe+i8nHfkESPCcY8EVdorXrWYrUXnousUiibB26IgOKiDiS8i8KDxIhBZb"

    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/flaskprogram"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    SESSION_TYPE = "redis"
    SESSION_USE_SIGNER = True
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 86400 * 2
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发模式下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产模式下的配置"""
    DEBUG = False
    LOG_LEVEL = logging.ERROR


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}


