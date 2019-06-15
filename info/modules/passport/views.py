# import logging
import random
import re

from datetime import datetime
from flask import abort, jsonify
from flask import current_app
from flask import json
from flask import make_response
from flask import request
from flask import session

from info import constants, db
from info import redis_store
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.response_code import RET
from . import passport_blu
from info.utils.captcha.captcha import captcha


@passport_blu.route('/logout')
def logout():
    """
    退出登录
    :return:
    """
    # pop是移除session中的数据(dict)
    # pop 会有一个返回值，如果要移除的key不存在，就返回None
    session.pop('user_id', None)
    session.pop('mobile', None)
    session.pop('nick_name', None)

    return jsonify(errno=RET.OK, errmsg="退出成功")


@passport_blu.route('/login', methods=["POST"])
def login():
    """
    登录
    1. 获取参数
    2. 校验参数
    3. 校验密码是否正确
    4. 保存用户的登录状态
    5. 响应
    :return:
    """

    # 1. 获取参数
    params_dict = request.json
    mobile = params_dict.get("mobile")
    password = params_dict.get("password")

    # 2. 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验手机号是否正确
    if not re.match('1[35678]\\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 3. 校验密码是否正确
    # 先查询出当前是否有指定手机号的用户
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    # 校验登录的密码和当前用户的密码是否一致
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg="用户名或者密码错误")

    # 4. 保存用户的登录状态
    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    user.last_login = datetime.now()

    # 如果在视图函数中，对模型身上的属性有修改，那么需要commit到数据库保存
    # 但是其实可以不用自己去写 db.session.commit(),前提是对SQLAlchemy有过相关配置

    # try:
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     current_app.logger.error(e)

    # 5. 响应
    return jsonify(errno=RET.OK, errmsg="登录成功")


@passport_blu.route("/register", methods=["POST"])
def register():
    # 注册的逻辑
    # 1. 获取参数

    params_dict = request.json
    mobile = params_dict.get("mobile")
    smscode = params_dict.get("smscode")
    password = params_dict.get("password")
    # 2. 校验参数
    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="请确认参数")
    if not re.match("1[35678]\\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="请填写正确的手机号")

    # 3. 取到服务器保存的真实的短信验证码内容
    try:
        real_sms_code = redis_store.get("SMS_" + mobile)
    except Exception as e:
        current_app.logging.error(e)
    # 4. 校验用户输入的短信验证码内容和真实验证码内容是否一致
    if real_sms_code != smscode:
        print(real_sms_code, smscode)
        return jsonify(errno=RET.DATAERR, errmsg="请填写正确的短信验证码")
    # 5. 如果一致，初始化 User 模型，并且赋值属性
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password
    user.last_login = datetime.now()
    # 6. 将 user 模型添加数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据存储失败")
    # 7. 返回响应
    session["mobile"] = user.mobile
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name

    return jsonify(errno=RET.OK, errmsg="注册成功")


@passport_blu.route("/sms_code", methods=["POST"])
def send_sms_code():
    # return jsonify(errno=RET.OK, errmsg="发送成功")
    # params_dict = json.loads(request.data)
    params_dict = request.json

    mobile = params_dict.get("mobile")
    image_code = params_dict.get("image_code")
    image_code_id = params_dict.get("image_code_id")

    if not all([mobile, image_code, image_code_id]):
        return jsonify(errorno=RET.PARAMERR, errmsg="参数错误")

    if not re.match("1[356789]\\d{9}", mobile):
        return jsonify(errorno=RET.PARAMERR, errmsg="手机号码格式不正确")

    try:
        real_image_code = redis_store.get("imageCodeId_" + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errerno=RET.DBERR, errmsg="数据查询失败")

    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码过期")

    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg="验证码错误")

    sms_code_str = "%06d" % random.randint(0, 99999999)
    current_app.logger.debug("短信验证码的内容是 %s" % sms_code_str)

    # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 6], "1")
    #
    # if result != 0:
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送失败")

    try:
        redis_store.set("SMS_" + mobile, sms_code_str, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="手机验证码保存失败")

    return jsonify(errno=RET.OK, errmsg="发送成功")


@passport_blu.route("/image_code")
def get_image_code():
    # 1.取到参数
    image_code_id = request.args.get("imageCodeId", "None")
    # 2.判断参数是否有值
    if not image_code_id:
        abort(403)
    # 3.生成图片验证码
    name, text, image = captcha.generate_captcha()
    current_app.logger.debug("图片验证码内容是：%s" % text)
    # 4.保存参数验证码键值对到redis
    try:
        redis_store.set("imageCodeId_" + image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        # logging.error(e)
        abort(500)
    # 5.返回验证码图片
    response = make_response(image)
    response.headers["Content-Type"] = "image/jpg"
    return response
