import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from flask_wtf.csrf import generate_csrf

from config import Config, config


db = SQLAlchemy()
redis_store = None  # type: StrictRedis


def setup_log(config_name):
    """配置日志"""

    logging.basicConfig(level=config[config_name].LOG_LEVEL)
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    formatter = logging.Formatter("%(levelname)s %(filename)s: %(lineno)d %(message)s")
    file_log_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    """通过传入不同的配置名字，初始化其对应配置的应用实例"""

    setup_log(config_name)
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    global redis_store
    redis_store = redis.StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT, decode_responses=True)
    # CSRFProtect(app)
    Session(app)

    # @app.after_request
    # def after_request(response):
    #     # 生成随机的csrf_token的值
    #     csrf_token = generate_csrf()
    #     # 设置一个cookie
    #     response.set_cookie("csrf_token", csrf_token)
    #     return response

    setup_log(config_name)

    from info.modules.index import index_blu
    app.register_blueprint(index_blu)

    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    return app



