from flask import current_app
from flask import g
from flask import render_template
from flask import request, jsonify
from flask import session

from info import constants
from info.models import News, Category, User
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blu


# 新闻模板渲染
@news_blu.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    # 查询用户登陆信息
    user = g.user

    # 右侧的新闻排行逻辑
    news_clicks_list = []
    try:
        news_clicks_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in news_clicks_list:
        news_dict_li.append(news.to_basic_dict())

    categories = Category.query.all()
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())

    data = {
        "user": user.to_dict() if user else None,
        "news_dict_li": news_dict_li
    }

    return render_template("news/detail.html", data=data)
