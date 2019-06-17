from flask import g, jsonify
from flask import redirect
from flask import render_template
from flask import request

from info.modules.profiles import profiles_blu
from info.utils.common import user_login_data
from info.utils.response_code import RET


@profiles_blu.route("/base_info", methods=["GET", "POST"])
@user_login_data
def base_info():
    # get 请求方式
    if request.method == "GET":
        return render_template("news/user_base_info.html", data={"user": g.user.to_dict()})

    # 修改用户信息
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERRK, errmsg="参数错误")

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
