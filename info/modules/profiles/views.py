import re

from flask import current_app
from flask import g, jsonify
from flask import redirect
from flask import render_template
from flask import request

from info import constants
from info.models import User, Category, News
from info.modules.profiles import profiles_blu
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET

from info import db


# 新闻发布
@profiles_blu.route("/news_release", methods=["GET", "POST"])
@user_login_data
def news_release():
    if request.method == "GET":

        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        category_dict_li = []
        for category in categories:
            category_dict_li.append(category.to_dict())

        category_dict_li.pop(0)

        data = {
            "categories":category_dict_li
        }
        return render_template("news/user_news_release.html", data=data)

    else:
        # 1. 获取要提交的数据
        # 标题
        title = request.form.get("title")
        # 新闻来源
        source = "个人发布"
        # 摘要
        digest = request.form.get("digest")
        # 新闻内容
        content = request.form.get("content")
        # 索引图片
        index_image = request.files.get("index_image")
        # 分类id
        category_id = request.form.get("category_id")

        # 校验参数
        # 2.1 判断数据是否有值
        if not all([title, source, digest, content, index_image, category_id]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

        try:
            category_id = int(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="新闻分类参数错误")

        try:
            index_image_data = index_image.read()
            key = storage(index_image_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="新闻分类参数错误")

        news = News()
        news.title = title
        news.source = source
        news.digest = digest
        news.content = content
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
        news.category_id = category_id
        news.user_id = g.user.id
        news.status = 1

        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

        return jsonify(errno=RET.OK, errmsg="OK")


# 用户收藏
@profiles_blu.route("/collection")
@user_login_data
def collection():
    user = g.user
    page = request.args.get("page", 1)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        current_page = paginate.page
        total_page = paginate.pages
        news_list = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_dict())

    data = {
        "current_page": current_page,
        "total_page": total_page,
        "collection": news_dict_li
    }

    return render_template("news/user_collection.html", data=data)


# 密码修改
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


# 更新头像
@profiles_blu.route("/pic_info", methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        return render_template("news/user_pic_info.html", data={"user": g.user.to_dict()})

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
    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url":constants.QINIU_DOMIN_PREFIX + key})


# 个人基本资料页面
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


# 判断用户是否登陆进而跳转页面
@profiles_blu.route("/user_info")
@user_login_data
def user_info():
    # 判断用户是否登陆
    user = g.user
    if not user:
        return redirect("/")

    data = {"user": user.to_dict()}
    return render_template("news/user.html", data=data)
