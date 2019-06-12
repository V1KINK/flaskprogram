# import logging
from flask import abort
from flask import current_app
from flask import request

from info import constants
from info import redis_store
from . import passport_blu
from info.utils.captcha.captcha import captcha


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
    return image
