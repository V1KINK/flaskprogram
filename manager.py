import redis
from flask import Flask, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
# from flask_script import Manager
from redis import StrictRedis


class Config(object):
    DEBUG = True

    SECRET_KEY = "afdgdgdfhadfgjh"

    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/flaskprogram"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    SECRET_TYPE = "redis"
    SESSION_USE_SIGNER = True
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 86400 * 2


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
CSRFProtect(app)
Session(app)


@app.route("/")
def index():
    session["name"] = "itheima"
    return "index"


if __name__ == '__main__':
    app.run()
