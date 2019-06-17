from flask import g
from flask import redirect
from flask import render_template

from info.modules.profiles import profiles_blu
from info.utils.common import user_login_data


@profiles_blu.route("/user_info")
@user_login_data
def user_info():
    # 判断用户是否登陆
    user = g.user
    if not user:
        return redirect("/")

    data = {"user": user.to_dict()}
    return render_template("news/user.html", data=data)
