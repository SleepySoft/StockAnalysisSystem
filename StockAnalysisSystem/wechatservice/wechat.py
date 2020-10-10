import time
import hashlib
import traceback

import requests
import xmltodict
from flask import Flask, request, make_response


class WeChat:
    SUPPORT_MSG = [
        'text', 'image', 'voice', 'amr', 'video', 'shortvideo', 'location', 'link'
    ]

    def __init__(self, token: str = ''):
        self.__token = token
        self.__app_id = ''
        self.__app_secret = ''
        self.__logger = print
        self.__msg_handler = {}

    def set_token(self, token: str = ''):
        self.__token = token

    def set_app_id(self, appid: str = ''):
        self.__app_id = appid

    def set_app_secret(self, appsecret: str = ''):
        self.__app_secret = appsecret

    def set_logger(self, logger: any):
        self.__logger = logger

    def set_msg_handler(self, msg_type: str, handler: any) -> bool:
        if msg_type not in WeChat.SUPPORT_MSG:
            self.log('Error: WeChat does not support message type: %s' % msg_type)
            return False
        if msg_type in self.__msg_handler.keys():
            self.log('Warning: Message type %s handler already exists: %s' % msg_type)
        self.__msg_handler[msg_type] = handler

    # ------------------------------------------------------------------------------------------

    def handle_request(self, flask_request: request):
        if not self.check_authentication(flask_request):
            return ''

        if flask_request.method == 'GET':
            print('-> GET')
            args = flask_request.args
            echostr = args.get('echostr', '')
            return echostr

        elif flask_request.method == 'POST':
            print('-> POST')
            return self.dispatch_message(flask_request)

    def dispatch_message(self, flask_request: request) -> str:
        req_data = flask_request.data
        xml_dict = xmltodict.parse(req_data)
        msg_dict = xml_dict.get('xml')

        print('  Content: ' + str(msg_dict))

        response_content = None
        msg_type = msg_dict.get('MsgType')
        handler = self.__msg_handler.get(msg_type, None)

        if handler is not None:
            response_content = handler(flask_request, msg_dict)

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

    def check_authentication(self, flask_request: request) -> bool:
        args = flask_request.args

        nonce = args.get('nonce')
        signature = args.get('signature')
        timestamp = args.get('timestamp')

        if nonce is None is None or signature is None or timestamp is None:
            print('Authentication data missing.')
            return False

        sign_arr = [self.__token, timestamp, nonce]
        sign_arr.sort()
        sign_str = ''.join(sign_arr)
        hashcode = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()

        if hashcode == signature:
            print('Signature match.')
            return True
        else:
            print('Signature not match.')
            return False

    def get_access_token(self) -> str:
        if self.__app_id == '' or self.__app_secret == '':
            self.log('Appid and Appsecret are must fields.')
            return ''
        uri = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % \
              (self.__app_id, self.__app_secret)
        r = requests.get(uri)
        resp = r.content
        return ''

    # ------------------------------------------------------------------------------------------

    def log(self, text: str):
        if self.__logger is not None:
            self.__logger(text)


# ----------------------------------------------------------------------------------------------------------------------

def test_get_access_token(wechat: WeChat):
    wechat.get_access_token()


if __name__ == '__main__':
    app = Flask(__name__)
    wechat = WeChat()

    wechat.set_token('')
    wechat.set_app_id('')
    wechat.set_app_secret('')

    @app.route('/wx', methods=['GET', 'POST'])
    def wechat_entry():
        print('-> Request /wx')
        response = wechat.handle_request(request)
        return response

    try:
        app.run(host='0.0.0.0', port=8000, debug=True)
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass




