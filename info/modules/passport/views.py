# import logging
import random
import re

from flask import abort, jsonify
from flask import current_app
from flask import json
from flask import make_response
from flask import request

from info import constants
from info import redis_store
from info.libs.yuntongxun.sms import CCP
from info.utils.response_code import RET
from . import passport_blu
from info.utils.captcha.captcha import captcha


@passport_blu.route("/sms_code")
def send_sms_code():
    # params_dict = json.loads(request.data)
    params_dict = request.json

    mobile = params_dict.get("mobile")
    image_code = params_dict.get("image_dict")
    image_code_id = params_dict.get("iamge_dict_id")

    if not all([mobile, image_code, image_code_id]):
        return jsonify(errorno=RET.PARAMERR, errmsg="参数错误")

    if not re.match("1[356789]\\d{9}", mobile):
        return jsonify(errorno=RET.PARAMERR, errmsg="手机号码格式不正确")

    try:
        real_image_code = redis_store.get("ImageCodeId_" + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errerno=RET.DBERR, errmsg="数据查询失败")

    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码过期")

    if real_image_code.upper() != image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg="验证码错误")

    sms_code_str = "%06d" % random.randint(0, 99999999)
    current_app.logger.debug("短信验证码的内容是 %s" % sms_code_str)

    result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 6], "1")

    if result != 0:
        return jsonify(errno=RET.THIRDERR, errmsg="发送失败")

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
