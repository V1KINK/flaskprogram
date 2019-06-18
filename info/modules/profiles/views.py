import re

from flask import current_app
from flask import g, jsonify
from flask import redirect
from flask import render_template
from flask import request

from info import constants
from info.models import User
from info.modules.profiles import profiles_blu
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET


@profiles_blu.route("/pass_info", methods=["GET", "POST"])
@user_login_data
def pass_info():
    if request.method == "GET":
        return render_template("news/user_pass_info.html")

    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")
    # confirm_password = request.json.get("confirm_password")

    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # if new_passwd != confirm_passwd:
    #     return jsonify(errno=RET.PARAMERR, errmsg="两次输入的密码不一致")

    if not re.match("^(?![0-9]+$)(?![a-zA-Z]+$)(?![_]+$)[0-9A-Za-z_]{6,10}$", new_password):
        return jsonify(errno=RET.PARAMERR, errmsg="密码只能由字母数字下划线组成")

    user = g.user
    if user.check_password(new_password):
        return jsonify(errno=RET.PARAMERR, errmsg="密码错误")

    user.password = new_password
    return jsonify(errno=RET.OK, errmsg="保存成功")


@profiles_blu.route("/pic_info", methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        return render_template("news/user_base_info.html", data={"user": g.user.to_dict()})

    try:
        avatar = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        key = storage(avatar)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传头像失败")

    user.avatar_url = key
    return jsonify(errno=RET.OK, errmsg="OK", avatar_url=constants.QINIU_DOMIN_PREFIX + key)


@profiles_blu.route("/base_info", methods=["GET", "POST"])
@user_login_data
def base_info():
    # get 请求方式
    if request.method == "GET":
        return render_template("news/user_base_info.html", data={"user": g.user.to_dict()})

    # post 修改用户信息
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = g.user
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    return jsonify(errno=RET.OK, errmsg="OK")


@profiles_blu.route("/user_info")
@user_login_data
def user_info():
    # 判断用户是否登陆
    user = g.user
    if not user:
        return redirect("/")

    data = {"user": user.to_dict()}
    return render_template("news/user.html", data=data)
