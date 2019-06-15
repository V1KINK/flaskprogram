from flask import render_template
from flask import request, jsonify

from info.utils.response_code import RET
from . import news_blu


# 新闻模板渲染
@news_blu.route("/<int:news_id>")
def news_detail(news_id):
    # news_id = request.json.get("news_id")
    # if not news_id:
    #     return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    return render_template("news/detail.html")
