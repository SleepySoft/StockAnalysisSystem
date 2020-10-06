import hashlib
import time

import xmltodict
from flask import request
from StockAnalysisSystem.core.config import Config


# ----------------------------------------------------------------------------------------------------------------------

def handle_command(msg_dict: dict) -> (bool, str):
    return False, ''


def handle_analysis(msg_dict: dict) -> (bool, str):
    content = msg_dict.get('Content')
    return True, ('<a href="http://211.149.229.160/analysis?security=%s">查看分析结果</a>' % content)


def handle_text_message(msg_dict: dict) -> str:
    ret, resp = handle_command(msg_dict)
    if ret:
        return resp
    ret, resp = handle_analysis(msg_dict)
    if ret:
        return resp
    return ''


def dispatch_wechat_message(flask_request: request) -> str:
    req_data = flask_request.data
    xml_dict = xmltodict.parse(req_data)
    msg_dict = xml_dict.get('xml')

    print('  Content: ' + str(msg_dict))

    response_content = None
    msg_type = msg_dict.get('MsgType')

    if msg_type == 'text':
        response_content = handle_text_message(msg_dict)
    elif msg_type == 'image':
        pass
    elif msg_type == 'image':
        pass
    elif msg_type == 'voice':
        pass
    elif msg_type == 'amr':
        pass
    elif msg_type == 'video':
        pass
    elif msg_type == 'shortvideo':
        pass
    elif msg_type == 'location':
        pass
    elif msg_type == 'link':
        pass

    if response_content is not None and response_content != '':
        response = {
            'ToUserName': msg_dict.get('FromUserName'),
            'FromUserName': msg_dict.get('ToUserName'),
            'CreateTime': int(time.time()),
            'MsgType': msg_type,
            'Content': response_content,
        }
        response_xml = xmltodict.unparse({"xml": response})
        return response_xml
    else:
        return ''


def check_wechat_authentication(flask_request: request) -> bool:
    args = flask_request.args

    nonce = args.get('nonce')
    signature = args.get('signature')
    timestamp = args.get('timestamp')

    if nonce is None is None or signature is None or timestamp is None:
        print('Authentication data missing.')
        return False

    sign_arr = [WECHAT_TOKEN, timestamp, nonce]
    sign_arr.sort()
    sign_str = ''.join(sign_arr)
    hashcode = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()

    if hashcode == signature:
        print('Signature match.')
        return True
    else:
        print('Signature not match.')
        return False


# ----------------------------------------------------------------------------------------------------------------------

WECHAT_TOKEN = ''


def handle_request(flask_request: request):
    if not check_wechat_authentication(flask_request):
        return ''

    if flask_request.method == 'GET':
        print('-> GET')
        args = flask_request.args
        echostr = args.get('echostr', '')
        return echostr

    elif flask_request.method == 'POST':
        print('-> POST')
        return dispatch_wechat_message(flask_request)


# ----------------------------------------------------------------------------------------------------------------------

def load_config(config: Config):
    global WECHAT_TOKEN
    WECHAT_TOKEN = config.get('wechat_token')
    if WECHAT_TOKEN == '' or WECHAT_TOKEN is None:
        print('Warning: Wechat token is empty.')


def init(config: Config):
    load_config(config)












