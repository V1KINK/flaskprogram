from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info.models import User
from info.utils.response_code import RET
from . import admin_blu


@admin_blu.route("/index")
def index():
    return render_template("admin/index.html")


@admin_blu.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
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
