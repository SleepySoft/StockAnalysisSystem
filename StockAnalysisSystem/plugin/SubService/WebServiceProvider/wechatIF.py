import os
import time
import hashlib
from flask import request

from StockAnalysisSystem.core.config import Config
from StockAnalysisSystem.core.Utility.relative_import import RelativeImport

with RelativeImport(__file__):
    from wechat import WeChat
    from service_provider import ServiceProvider


wechat: WeChat = None
service_provider: ServiceProvider = None


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
    username = parameters[0] if len(parameters) > 0 else ''
    password = parameters[1] if len(parameters) > 1 else ''

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
    username = parameters[0] if len(parameters) > 0 else ''
    if username != '' and username in SasUserWxUserDict.keys():
        wechat_user = SasUserWxUserDict[username]
        wechat.get_user_manager().update_user_session(wechat_user, 'login', 0)
        del SasUserWxUserDict[username]
        del WxUserSasUserDict[wechat_user]
        return 'Logoff successful'
    else:
        return ''


# ----------------------------------------------------------------------------------------------------------------------

def parse_command(text: str) -> (str, str):
    parts = text.split()
    command = parts[0] if len(parts) > 0 else ''
    parameters = parts[1:] if len(parts) > 1 else ''
    return command, parameters


def handle_command(flask_request: request, msg_dict: dict) -> (bool, str):
    content: str = msg_dict.get('Content', '')
    command, parameters = parse_command(content)

    if command.lower() == 'test':
        return True, handle_cmd_test(parameters, flask_request, msg_dict)
    if command.lower() == 'login':
        return True, handle_cmd_login(parameters, flask_request, msg_dict)
    if command.lower() == 'logoff':
        return True, handle_cmd_logoff(parameters, flask_request, msg_dict)

    return False, ''


def handle_analysis(flask_request: request, msg_dict: dict) -> (bool, str):
    security = msg_dict.get('Content', '')
    url = service_provider.get_security_analysis_result_url(security)
    if url != '':
        return True, ('<a href="%s">查看分析结果</a>' % url)
    else:
        return security.isdigit(), ('没有股票[%s]的分析结果' % security)


def handle_text_message(flask_request: request, msg_dict: dict) -> str:
    ret, resp = handle_command(flask_request, msg_dict)
    if ret:
        return resp
    ret, resp = handle_analysis(flask_request, msg_dict)
    if ret:
        return resp
    return ''


# ----------------------------------------------------------------------------------------------------------------------

def handle_request(flask_request: request) -> str:
    global wechat
    return wechat.handle_request(flask_request)


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


def init(provider: ServiceProvider, config: Config):
    global service_provider
    service_provider = provider

    global wechat
    wechat = WeChat()
    load_config(config)

    wechat.set_msg_handler('text', handle_text_message)













