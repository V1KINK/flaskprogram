import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis

from config import Config, config


db = SQLAlchemy()
redis_store = None  # type: StrictRedis


def create_app(config_name):
    """通过传入不同的配置名字，初始化其对应配置的应用实例"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    global redis_store
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)
    CSRFProtect(app)
    Session(app)

    from info.modules.index import index_blu
    app.register_blueprint(index_blu)

    setup_log(config_name)
    app = Flask(__name__)

    return app


def setup_log(config_name):
    """配置日志"""

    logging.basicConfig(level=config[config_name].LOG_LEVEL)
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    formatter = logging.Formatter("%(levelname)s %(filename)s: %(lineno)d %(message)s")
    file_log_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_log_handler)

