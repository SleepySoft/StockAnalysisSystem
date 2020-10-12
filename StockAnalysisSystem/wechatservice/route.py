import hashlib
from flask import request

from .wechat import WeChat
from StockAnalysisSystem.core.config import Config


wechat: WeChat = None

SasUserWxUserDict = {

}

WxUserSasUserDict = {

}


# ----------------------------------------------------------------------------------------------------------------------

def handle_cmd_test(parameters: str, flask_request: request, msg_dict: dict) -> str:
    wechat_user = msg_dict.get('FromUserName', '')
    if wechat_user not in WxUserSasUserDict.keys():
        return ''
    user_mgr = wechat.get_user_manager()
    user_lst = user_mgr.get_user_list()
    if len(user_lst) > 0:
        wechat.send_user_message(user_lst[0], 'Hello from Sleepy')
    return 'Test Execute Done'


def handle_cmd_login(parameters: str, flask_request: request, msg_dict: dict) -> str:
    parts = parameters.split(',')
    username = (parts[0] if len(parts) > 0 else '').strip()
    password = (parts[1] if len(parts) > 1 else '').strip()

    passwd_sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest()

    if username == 'Sleepy' and passwd_sha1 == '4181a3ababceb12d8cf21523e7eafefb46f7326f':
        wechat_user = msg_dict.get('FromUserName', '')
        if wechat_user != '':
            SasUserWxUserDict[username] = wechat_user
            WxUserSasUserDict[wechat_user] = username
            wechat.get_user_manager().update_user_session(wechat_user, 'login', time.time())
            return 'Login Successful'
    return ''


def handle_cmd_logoff(parameters: str, flask_request: request, msg_dict: dict) -> str:
    username = parameters.strip()
    if username != '' and username in SasUserWxUserDict.keys():
        wechat_user = SasUserWxUserDict[username]
        wechat.get_user_manager().update_user_session(wechat_user, 'login', 0)
        del SasUserWxUserDict[username]
        del WxUserSasUserDict[wechat_user]


# ----------------------------------------------------------------------------------------------------------------------

def parse_command(text: str) -> (str, str):
    parts = text.split(':')
    command = (parts[0] if len(parts) > 0 else '').strip()
    parameters = (parts[1] if len(parts) > 1 else '').strip()
    return command, parameters


def handle_command(flask_request: request, msg_dict: dict) -> (bool, str):
    content: str = msg_dict.get('Content', '')
    command, parameters = parse_command(content)

    if command == 'test':
        return True, handle_cmd_test(parameters, flask_request, msg_dict)
    if command == 'login':
        return True, handle_cmd_login(parameters, flask_request, msg_dict)
    if command == 'logoff':
        return True, handle_cmd_logoff(parameters, flask_request, msg_dict)

    return False, ''


def handle_analysis(flask_request: request, msg_dict: dict) -> (bool, str):
    content = msg_dict.get('Content', '')
    return True, ('<a href="http://211.149.229.160/analysis?security=%s">查看分析结果</a>' % content)


def handle_text_message(flask_request: request, msg_dict: dict) -> str:
    ret, resp = handle_command(flask_request, msg_dict)
    if ret:
        return resp
    ret, resp = handle_analysis(flask_request, msg_dict)
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













