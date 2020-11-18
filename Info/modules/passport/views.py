from datetime import datetime
import random
import re
from Info.utils.captcha.captcha import captcha
from Info.utils.response_code import RET
from . import passport_blue
from Info import redis_store, constants, db, redis_login_image
from flask import request, current_app, make_response, jsonify, session
from Info.models import User


@passport_blue.route('/login', methods=['POST'])
def login():
    """
    1. 获取参数
    2. 校验参数,为空校验
    3. 通过用户手机号,到数据库查询用户对象
    4. 判断用户是否存在
    5. 校验密码是否正确
    6. 将用户的登陆信息保存在session中
    7. 返回响应
    :return:
    """
    # 1.获取参数
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    input_code = request.json.get("input_code")
    ImageCode = request.json.get("image_code")
    # current_app.logger.debug("输入的验证码是：%s" %input_code)
    # 2.校验参数, 为空校验
    if not all([mobile, password, input_code]):
        return jsonify(errno=RET.PARAMERR, errmsg="输入有效信息")
    # 3.取出图片验证码并且验证是否正确
    try:
        redis_image_code1 = redis_login_image.get("image_code:%s" % ImageCode)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="图片验证码取出失败")
    if not redis_image_code1:
        current_app.logger.debug("验证码是:%s" % redis_image_code1)
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已经过期")
    if input_code.upper() != redis_image_code1.upper():
        return jsonify(errno=RET.DATAERR,errmsg="图片验证码填写错误")
    try:
        redis_store.delete("image_code:%s"%ImageCode)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="删除redis图片验证码失败")
    # 4.通过用户手机号, 到数据库查询用户对象
    try:
        user = User()
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户失败")
    # 5.判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="该用户不存在")
    # 6.校验密码是否正确
    if not user.check_password(password):
        return jsonify(errno=RET.DATAERR, errmsg="密码输入错误")
    # 7.将用户的登陆信息保存在session中
    session["user_id"] = user.id
    user.last_login = datetime.now()
    user.login_ip = request.remote_addr
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
    # 7.返回响应
    return jsonify(errno=RET.OK, errmsg="恭喜您！登陆成功！")


@passport_blue.route('/logout', methods=["POST"])
def logout():
    """
    1.清除session信息
    2.返回响应
    :return:
    """
    # 1.清除session信息
    session.pop("user_id", None)
    # 2.返回响应
    return jsonify(errno=RET.OK, errmsg="退出成功")


@passport_blue.route('/register', methods=['POST'])
def register():
    # json_data = request.data
    # dict_data = json.loads
    # 可以替换掉上面的两句话
    dict_data = request.json
    # dict_data = request.get_json() #等价于上面一句话
    # current_app.logger.debug("前端传入的字典是 = %s" % dict_data)
    mobile = dict_data.get("mobile")
    sms_code = dict_data.get("sms_code")
    password = dict_data.get("password")
    re_password = dict_data.get("re_password")

    # 2. 校验参数,为空校验
    if not all([mobile, sms_code, password, re_password]):
        # current_app.logger.debug("输入的手机号 = %s" % mobile)
        # current_app.logger.debug("输入的验证码是 = %s" % sms_code)
        # current_app.logger.debug("输入的密码是 = %s" % password)
        # current_app.logger.debug("再次输入的密码是 = %s" % re_password)
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 3. 手机号作为key取出redis中的短信验证码
    try:
        redis_sms_code = redis_store.get("sms_code:%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="短信验证码取出失败")

    # 4. 判断短信验证码是否过期
    if not redis_sms_code:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码已经过期")

    # 5. 判断短信验证码是否正确
    if sms_code != redis_sms_code:
        # current_app.logger.debug("存储的短信验证码是 = %s" % redis_sms_code)
        # current_app.logger.debug("输入短信验证码是 = %s" % sms_code)
        # current_app.logger.debug("再次输入的密码是 = %s" % re_password)
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码填写错误")

    # 6. 删除短信验证码
    try:
        redis_store.delete("sms_code:%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="短信验证码删除失败")

    # 7. 创建用户对象
    user = User()

    # 8. 设置用户对象属性
    user.nick_name = mobile
    # user.password_hash = password
    user.password = password  # 密码的加密处理
    user.mobile = mobile
    user.signature = "该用户很懒,什么都没写"
    # user.login_ip = "123"
    # login_ip = request.user_agent.string
    # current_app.logger.debug("登录的地址是:%s"%login_ip)

    # 9. 保存用户到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="用户注册失败")

    # 10. 返回响应
    return jsonify(errno=RET.OK, errmsg="注册成功")


@passport_blue.route('/sms_code', methods=['POST'])
def sms_code():
    """
    1. 获取参数
    2. 参数的为空校验
    3. 校验手机的格式
    4. 通过图片验证码编号获取,图片验证码
    5. 判断图片验证码是否过期
    6. 判断图片验证码是否正确
    7. 删除redis中的图片验证码
    8. 生成一个随机的短信验证码, 调用ccp发送短信,判断是否发送成功
    9. 将短信保存到redis中
    10. 返回响应
    :return:
    """
    # 1. 获取参数
    # json_data = request.data
    # dict_data = json.loads(json_data)
    dict_data = request.json #reqeuts.get_json()

    mobile = dict_data.get("mobile")
    image_code = dict_data.get("image_code")
    image_code_id = dict_data.get("image_code_id")

    # 2. 参数的为空校验
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 3. 校验手机的格式
    if not re.match("1[3-9]\d{9}",mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机号的格式错误")

    # 4. 通过图片验证码编号获取,图片验证码
    try:
        redis_image_code = redis_store.get("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="操作redis失败")

    # 5. 判断图片验证码是否过期
    if not redis_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已经过期")

    # 6. 判断图片验证码是否正确
    if image_code.upper() != redis_image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码填写错误")

    # 7. 删除redis中的图片验证码
    try:
        redis_store.delete("image_code:%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="删除redis图片验证码失败")

    # 8. 生成一个随机的短信验证码, 调用ccp发送短信,判断是否发送成功
    sms_code = "%06d" % random.randint(0, 999999)
    current_app.logger.debug("短信验证码是 = %s" % sms_code)
    current_app.logger.debug("图片验证码是%s" % redis_image_code)
    # ccp = CCP()
    # 参数1mobile: 要给哪个手机号发送短信    参数2: ["验证码",有效期]  参数3: 模板编号默认就是1
    # 【云通讯】您使用的是云通讯短信模板，您的验证码是{1}，请于{2}分钟内正确输入
    # result = ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)

    # if result == -1:
    #     return jsonify(errno=RET.DATAERR,errmsg="短信发送失败")

    # 9. 将短信保存到redis中
    try:
        redis_store.set("sms_code:%s" % mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="图片验证码保存到redis失败")

    # 10. 返回响应
    return jsonify(errno=RET.OK, errmsg="短信发送成功")


@passport_blue.route('/image_code')
def image_code():
    cur_id = request.args.get("cur_id")  # 前端生成的cur_id
    pre_id = request.args.get("pre_id")  # 前端生成的pre_id
    name, text, image_data = captcha.generate_captcha()  # 调用生成验证码方法

    try:
        redis_store.set("image_code:%s" % cur_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
        if pre_id:
            redis_store.delete("image_code:%s" % pre_id)
    except Exception as e:
        current_app.logger.error(e)
        return "图片"
    response = make_response(image_data)
    response.headers["Content-Type"] = "image/png"

    return response