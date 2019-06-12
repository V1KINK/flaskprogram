from flask import current_app
from flask import render_template

from info import redis_store
from . import index_blu


@index_blu.route("/")
def index():
    # redis_store.set("name", "itcast")
    return render_template("news/index.html")


# 在浏览器打开时默认访问根路由和 favicon.ico 图片作为网站的小图标
@index_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")
