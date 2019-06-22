import time
from datetime import datetime, timedelta

from flask import current_app, jsonify
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from info import constants
from info.models import User, News
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import admin_blu


@admin_blu.route("/news_review_action", methods=["POST"])
def news_review_action():
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not news:
        return jsonify(errno=RET.DBERR, errmsg="未查询到新闻数据")

    if action == "accept":
        news.status = 0
        print(news.status)
    else:
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请输入原因")
        news.reason = reason
        news.status = -1

    return jsonify(errno=RET.OK, errmsg="OK")


@admin_blu.route("/news_review_detail.html/<int:news_id>")
def news_review_detail(news_id):
    # id = request.args.get("news_id")
    # if not id:
    #     return render_template("admin/news_review_detail.html", data={"errmsg": "未查询到新闻数据"})

    news = None
    try:
        # news = News.query.filter(News.id == id).first()
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return render_template("admin/news_review_detail.html", data={"errmsg": "未查询到新闻数据"})

    data = {"news": news.to_dict()}

    return render_template("admin/news_review_detail.html", data=data)


@admin_blu.route('/news_review')
def news_review():
    page = request.args.get("p", 1)
    keyword = request.args.get("keyword", None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    filters = [News.status != 0]
    if keyword:
        filters.append(News.title.contains(keyword))

    try:
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_review_dict())

    context = {"total_page": total_page, "current_page": current_page, "news_list": news_dict_list}

    return render_template('admin/news_review.html', data=context)


@admin_blu.route("/user_list")
def user_list():
    page = request.args.get("page", 1)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    users = []
    current_page = 1
    total_page = 1

    try:
        paginate = User.query.filter(User.is_admin == False).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    user_dict_li = []

    for user in users:
        user_dict_li.append(user.to_dict())

    data = {
        "current_page": current_page,
        "total_page": total_page,
        "users": user_dict_li
    }

    return render_template("admin/user_list.html", data=data)


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
        count = User.query.filter(User.is_admin == False, User.create_time >= begin_date,
                                  User.create_time < end_date).count()
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
