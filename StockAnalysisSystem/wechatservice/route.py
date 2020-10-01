import hashlib
import time

import xmltodict
from flask import request
from StockAnalysisSystem.core.config import Config


# ----------------------------------------------------------------------------------------------------------------------

def handle_text_message(msg_dict: dict) -> str:
    content = msg_dict.get('Content')
    return '收到：' + content


def dispatch_wechat_message(flask_request: request) -> str:
    req_data = flask_request.data
    xml_dict = xmltodict.parse(req_data)
    msg_dict = xml_dict.get('xml')
    print(msg_dict)

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


# ----------------------------------------------------------------------------------------------------------------------

WECHAT_TOKEN = ''


def handle_request(flask_request: request):
    args = flask_request.args

    nonce = args.get('nonce')
    echostr = args.get('echostr')
    signature = args.get('signature')
    timestamp = args.get('timestamp')

    if nonce is None or echostr is None or signature is None or timestamp is None:
        print('Authentication data missing.')
        return 'errno', 403

    # 1. 将token、timestamp、nonce三个参数进行字典序排序
    sign_arr = [WECHAT_TOKEN, timestamp, nonce]
    sign_arr.sort()
    sign_str = ''.join(sign_arr)

    # 2. 将三个参数字符串拼接成一个字符串进行sha1加密
    sign_dig = hashlib.sha1(sign_str).hexdigest()

    # 3. 开发者获得加密后的字符串可与signature对比
    if sign_dig == signature:
        # 根据请求方式.返回不同的内容 ,如果是get方式,代表是验证服务器有效性
        if flask_request.method == 'GET':
            return echostr
        # 如果POST方式,代表是微服务器转发给我们的消息
        elif flask_request.method == 'POST':
            return dispatch_wechat_message(flask_request)
    else:
        return 'errno', 403


# ----------------------------------------------------------------------------------------------------------------------

def load_config():
    global WECHAT_TOKEN
    config = Config()
    config.load_config()
    WECHAT_TOKEN = config.get('wechat_token')
    if WECHAT_TOKEN == '':
        print('Warning: Wechat token is empty.')


def init():
    load_config()












