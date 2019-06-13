from flask import current_app
from flask import render_template
from flask import session

from info import redis_store
from info.models import User
from . import index_blu


@index_blu.route("/")
def index():
    # redis_store.set("name", "itcast")
    """
    显示首页
    1. 如果用户已经登录，将当前登录用户的数据传到模板中，供模板显示
    :return:
    """

    # 取到用户id
    user_id = session.get("user_id", None)
    user = None
    if user_id:
        # 尝试查询用户的模型
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    data = {
        "user": user.to_dict() if user else None
    }

    return render_template('news/index.html', data=data)


# 在浏览器打开时默认访问根路由和 favicon.ico 图片作为网站的小图标
@index_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")
