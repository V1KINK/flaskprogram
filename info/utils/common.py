import functools

from flask import current_app
from flask import g
from flask import session

from info.models import User


def do_index_class(index):
    if index == 0:
        return "first"

    if index == 1:
        return "second"

    if index == 2:
        return "third"

    return ""


def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id", None)
        user = None
        if user_id:
            # 尝试查询用户的模型
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user

        return f(*args, **kwargs)
    return wrapper

