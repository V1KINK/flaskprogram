from flask import abort
from flask import current_app
from flask import g
from flask import render_template
from flask import request, jsonify
from flask import session

from info import constants, db
from info.models import News, Category, Comment, CommentLike
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blu


@news_blu.route("/comment_like", methods=["POST"])
@user_login_data
def comment_like():
    # 新闻点赞
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="未登录用户")

    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="action参数错误")

    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not comment:
        return jsonify(errno=RET.DATAERR, errmsg="评论不存在")

    if action == "add":
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment_id).first()
        if not comment_like_model:
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment_id
            db.session.add(comment_like_model)
            comment.like_count += 1

    else:
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment_id).first()
        if comment_like_model:
            db.session.delete(comment_like_model)
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")

    return jsonify(errno=RET.OK, errmsg="OK")


@news_blu.route("/news_comment", methods=["POST"])
@user_login_data
def comment_news():
    # 新闻评论
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="未登录用户")

    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmu="未查询到新闻数据")

    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_content

    if parent_id:
        comment.parent_id = parent_id

    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())


@news_blu.route("/news_collect", methods=["POST"])
@user_login_data
def collect_news():
    # 点击收藏
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="未登录用户")

    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmu="未查询到新闻数据")

    if action == "collect":
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        if news in user.collection_news:
            user.collection_news.remove(news)

    return jsonify(errno=RET.OK, errmsg="操作成功")


# 新闻详情模板渲染
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
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    news_dict_li = []
    for news in news_clicks_list:
        news_dict_li.append(news.to_basic_dict())

    categories = Category.query.all()
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())

    # 查询新闻详情
    news = None

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not news:
        abort(404)

    news.clicks += 1

    is_collected = False

    if user:
        # if news in user.collection_news.all():    # uer.collection_news.all() 将数据查询出来返回列表
        if news in user.collection_news:  # uer.collection_news 为查询对象（sql语句）, 再被用到时才执行
            is_collected = True

    # 查询评论
    comments = []

    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    # 查询当前用户在当前新闻里点赞了哪些评论
    comment_like_ids = []
    if user:
        try:
            comment_ids = [comment.id for comment in comments]
            comment_likes = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                     CommentLike.comment_id.in_(comment_ids)).all()
            comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
        except Exception as e:
            current_app.logger.error(e)

    comment_dict_li = []
    for comment in comments:
        comment_dict = comment.to_dict()
        comment_dict["is_like"] = False
        if comment.id in comment_like_ids:
            comment_dict["is_like"] = True
        comment_dict_li.append(comment_dict)

    data = {
        "user": user.to_dict() if user else None,  # 如果用户登录则 user： user.to_dict, 否则 user = None
        "news_dict_li": news_dict_li,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "comments": comment_dict_li
    }

    return render_template("news/detail.html", data=data)
