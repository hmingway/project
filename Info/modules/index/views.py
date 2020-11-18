from Info.models import User, News, Category
from . import index_blue
from flask import current_app, render_template, session, jsonify

from ...utils.response_code import RET


@index_blue.route("/", methods=["GET", "POST"])
def hello_world():
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # #查询热门新闻
    # try:
    #     news = News.query.order_by(News.clicks.desc()).limit(10).all()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DEBBER, errmsg="获取新闻失败")
    # news_list = []
    # for item in news_list:
    #     news_list.append(item.to_dict())"news_list": news_list
    data = {
        #如果user有值，返回左边，都则返回右边
        "user_info": user.to_dict() if user else ""

    }
    return render_template("news/index.html", data=data)


@index_blue.route('/2.png')
def get_web_logo():
    return current_app.send_static_file('news/2.png')
