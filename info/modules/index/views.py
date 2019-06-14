from flask import current_app, jsonify
from flask import render_template
from flask import request
from flask import session

from info import redis_store
from info.models import User, News
from info.utils.response_code import RET
from . import index_blu


@index_blu.route("/news_list")
def news_list():

    cid = request.args.get("cid", "1")
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "10")

    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    filters = []
    if cid != 1:
        filters.append(News.category_id == cid)

    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    news_model_list = paginate.items
    total_pages = paginate.pages
    current_page = paginate.page

    news_dict_li = []
    for news in news_model_list:
        news_dict_li.append(news.to_basic_dict)

    data = {
        "total_pages": total_pages,
        "current_page": current_page,
        "news_dict_li": news_dict_li
    }

    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@index_blu.route("/")
def index():
    # redis_store.set("name", "itcast")
    """
    显示首页
    1. 如果用户已经登录，将当前登录用户的数据传到模板中，供模板显示
    :return:
    """
    # 显示用户是否登陆的逻辑
    # 取到用户id
    user_id = session.get("user_id", None)
    user = None
    if user_id:
        # 尝试查询用户的模型
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    news_page_list = []
    try:
        news_page_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in news_page_list:
        news_dict_li.append(news.to_basic_dict())

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li
    }

    return render_template('news/index.html', data=data)


# 在浏览器打开时默认访问根路由和 favicon.ico 图片作为网站的小图标
@index_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")
