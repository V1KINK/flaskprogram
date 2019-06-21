import time
from datetime import datetime, timedelta

from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info.models import User
from info.utils.common import user_login_data
from . import admin_blu


@admin_blu.route("/user_count")
def user_count():
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 月新赠数
    mon_count = 0
    t = time.localtime()
    begin_mon_data = datetime.strptime(("%d-%02d-01" % (t.tm_year, t.tm_mon)), "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= begin_mon_data).count()
    except Exception as e:
        current_app.logger.error(e)

    # 日新赠数
    day_count = 0
    t = time.localtime()
    begin_day_data = datetime.strptime(("%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time >= begin_day_data).count()
    except Exception as e:
        current_app.logger.error(e)

    # 折线图
    active_count = []
    active_time = []
    begin_today_data = datetime.strptime(("%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")

    for i in range(0, 31):
        begin_date = begin_today_data - timedelta(i)
        end_date = begin_today_data - timedelta(i - 1)
        count = User.query.filter(User.is_admin == False, User.create_time >= begin_date, User.create_time < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime("%Y-%m-%d"))

    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_count": active_count,
        "active_time": active_time
    }

    return render_template("admin/user_count.html", data=data)


@admin_blu.route("/index")
@user_login_data
def index():
    user = g.user
    return render_template("admin/index.html", data=user.to_dict())


@admin_blu.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":

        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)
        if user_id and is_admin:
            return redirect(url_for("admin.index"))

        return render_template("admin/login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    if not all([username, password]):
        return render_template("admin/login.html", errmsg="请输入用户名和密码")

    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="用户数据查询失败")

    if not user:
        return render_template("admin/login.html", errmsg="未查询到用户数据")

    if not user.check_password(password):
        return render_template("admin/login.html", errmsg="用户密码错误")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = user.is_admin

    return redirect(url_for("admin.index"))
