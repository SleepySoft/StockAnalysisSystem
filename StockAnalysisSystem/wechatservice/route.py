from flask import request

from .wechat import WeChat
from StockAnalysisSystem.core.config import Config


wechat: WeChat = None


# ----------------------------------------------------------------------------------------------------------------------

def handle_command(msg_dict: dict) -> (bool, str):
    return False, ''


def handle_analysis(msg_dict: dict) -> (bool, str):
    content = msg_dict.get('Content')
    return True, ('<a href="http://211.149.229.160/analysis?security=%s">查看分析结果</a>' % content)


def handle_text_message(flask_request: request, msg_dict: dict) -> str:
    ret, resp = handle_command(msg_dict)
    if ret:
        return resp
    ret, resp = handle_analysis(msg_dict)
    if ret:
        return resp
    return ''


# ----------------------------------------------------------------------------------------------------------------------

def handle_request(flask_request: request):
    global wechat
    wechat.handle_request(flask_request)


# ----------------------------------------------------------------------------------------------------------------------

def load_config(config: Config):
    wechat_token = config.get('wechat_token', '')
    wechat_app_id = config.get('wechat_app_id', '')
    wechat_app_secret = config.get('wechat_app_secret', '')

    print('Load config - WeChat Token: %s' % wechat_token)
    print('Load config - WeChat App ID: %s' % wechat_app_id)
    print('Load config - WeChat App Secret: %s' % wechat_app_id)

    global wechat
    wechat.set_token(wechat_token)
    wechat.set_app_id(wechat_app_id)
    wechat.set_app_secret(wechat_app_secret)


def init(config: Config):
    global wechat
    wechat = WeChat()
    load_config(config)

    wechat.set_msg_handler('text', handle_text_message)













