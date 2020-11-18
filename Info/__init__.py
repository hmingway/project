import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
# from flask_session import Session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis
from config import Config, config_dict

redis_login_image = None
redis_store = None
db = SQLAlchemy()


def create_app(config_name):

    app = Flask(__name__)
    config = config_dict.get(config_name)
    log_file(config.LEVEL_NAME)

    app.config.from_object(config)
    # global db
    db.init_app(app)

    global redis_store, redis_login_image
    redis_store = StrictRedis(host=config.REDIS_HOST,port=config.REDIS_PORT,decode_responses=True)
    redis_login_image = StrictRedis(host=config.REDIS_HOST,port=config.REDIS_PORT,decode_responses=True)

    Session(app)

    CSRFProtect(app)
    from Info.modules.index import index_blue
    app.register_blueprint(index_blue)


    #将函数添加到默认的过滤器列表中
    from Info.utils.commons import hot_news_first
    app.add_template_filter(hot_news_first,"my_filter")


    from Info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)

    # app.add_template_filter(hot_news_filter,"my_filter"
    @app.after_request
    def after_request(resp):
        # 调用系统方法,获取csrf_token
        csrf_token = generate_csrf()

        # 将csrf_token设置到cookie中
        resp.set_cookie("csrf_token", csrf_token)

        # 返回响应
        return resp
    return app


def log_file(LEVEL_NAME):
    # 设置日志的记录等级,常见的有四种,大小关系如下: DEBUG < INFO < WARNING < ERROR
    logging.basicConfig(level=LEVEL_NAME)  # 调试debug级,一旦设置级别那么大于等于该级别的信息全部都会输出
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)