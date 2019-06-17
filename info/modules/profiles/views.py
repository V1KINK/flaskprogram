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

    if request.method == "GET":
        return render_template("news/user_base_info.html", data={"user": g.user.to_dict()})


@profiles_blu.route("/user_info")
@user_login_data
def user_info():
    # 判断用户是否登陆
    user = g.user
    if not user:
        return redirect("/")

    data = {"user": user.to_dict()}
    return render_template("news/user.html", data=data)
