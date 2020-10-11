import json
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

    class User:
        def __init__(self, openid: str):
            self.open_id = openid
            self.last_message = None
            self.last_received = 0
            self.session = {}

    class UserManager:
        def __init__(self):
            self.__user_context = {}

        def clear(self):
            self.__user_context.clear()

        def get_user_list(self) -> [str]:
            return list(self.__user_context.keys())

        def update_user_session(self, user: str, key: str, val: any):
            user_ctx = self.get_user_context(user)
            if user_ctx is not None:
                user_ctx.session[key] = val

        def get_user_context(self, user: str):
            return self.__user_context.get(user, None)

        def update_user_context(self, msg_dict: dict):
            user = msg_dict.get('FromUserName', '')
            if user == '':
                return
            if user not in self.__user_context:
                user_ctx = WeChat.User(user)
                self.__user_context[user] = user_ctx
                print('New user: [%s]' % user)
            else:
                user_ctx = self.__user_context[user]
            user_ctx.last_message = msg_dict
            user_ctx.last_received = time.time()

    def __init__(self, token: str = ''):
        # Platform keys (keep secret)
        self.__token = token
        self.__app_id = ''
        self.__app_secret = ''

        # Access Token
        self.__access_token = ''
        self.__access_token_expired_ts = 0

        # User manage
        self.__record_user = True
        self.__user_manager = WeChat.UserManager()

        # Internal data
        self.__logger = print
        self.__msg_handler = {}

    def set_token(self, token: str = ''):
        self.__token = token

    def set_app_id(self, appid: str = ''):
        self.__app_id = appid

    def set_app_secret(self, appsecret: str = ''):
        self.__app_secret = appsecret

    def enable_user_record(self, enable: bool):
        self.__record_user = enable

    def set_logger(self, logger: any):
        self.__logger = logger

    def set_msg_handler(self, msg_type: str, handler: any) -> bool:
        if msg_type not in WeChat.SUPPORT_MSG:
            self.log('Error: WeChat does not support message type: %s' % msg_type)
            return False
        if msg_type in self.__msg_handler.keys():
            self.log('Warning: Message type %s handler already exists: %s' % msg_type)
        self.__msg_handler[msg_type] = handler

    def get_user_manager(self) -> UserManager:
        return self.__user_manager

    # ------------------------------------------------------------------------------------------

    def handle_request(self, flask_request: request):
        if not self.check_authentication(flask_request):
            return ''

        if flask_request.method == 'GET':
            args = flask_request.args
            echostr = args.get('echostr', '')
            return echostr

        elif flask_request.method == 'POST':
            return self.dispatch_message(flask_request)

    def dispatch_message(self, flask_request: request) -> str:
        req_data = flask_request.data
        xml_dict = xmltodict.parse(req_data)
        msg_dict = xml_dict.get('xml')

        print('  Content: ' + str(msg_dict))

        if self.__record_user:
            self.__user_manager.update_user_context(msg_dict)

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
        if self.__access_token == '' or self.__access_token_expired_ts <= int(time.time()):
            access_token, expires_in = self.fetch_access_token()
            if access_token is not None:
                self.__access_token = access_token
                self.__access_token_expired_ts = int(time.time() + expires_in * 0.9)
            else:
                self.__access_token = ''
                self.__access_token_expired_ts = 0
        return self.__access_token

    def fetch_access_token(self) -> (str, int):
        if self.__app_id == '' or self.__app_secret == '':
            self.log('Appid and Appsecret are must fields.')
            return ''
        uri = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % \
              (self.__app_id, self.__app_secret)
        r = requests.get(uri)
        resp = r.content
        resp_str = resp.decode('utf-8')
        resp_json = json.loads(resp_str)

        errmsg = resp_json.get('errmsg')
        errcode = resp_json.get('errcode')

        expires_in = resp_json.get('expires_in', 0)
        access_token = resp_json.get('access_token')

        if access_token is None:
            self.log('Get access token error: %s (code: %s)' % (errmsg, errcode))
            return '', 0
        else:
            return access_token, int(expires_in)

    # ------------------------------------------------------------------------------------------

    def send_user_message(self, user: str, message: str, msg_type: str='text') -> bool:
        user_context = self.__user_manager.get_user_context(user)
        if user_context is None:
            self.log('Error in Send message: User [%s] does not exist.' % user)
            return False

        access_token = self.get_access_token()
        if access_token == '':
            self.log('Error in Send message: Invalid Access Token.')
            return False

        message_dict = {
            'touser': user,
            'msgtype': msg_type,
            'text': {
                 'content': message
            }
        }
        message_xml = xmltodict.unparse(message_dict)

        uri = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=%s' % access_token
        resp = requests.post(uri, data=message_xml)

        return True

    # ------------------------------------------------------------------------------------------

    def log(self, text: str):
        if self.__logger is not None:
            self.__logger(text)


# ----------------------------------------------------------------------------------------------------------------------

def test_fetch_access_token(wechat: WeChat):
    wechat.fetch_access_token()


def test_send_user_message(wechat: WeChat):
    user_mgr = wechat.get_user_manager()
    user_lst = user_mgr.get_user_list()
    if len(user_lst) > 0:
        wechat.send_user_message(user_lst[0], 'Hello from Sleepy')


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

    test_fetch_access_token(wechat)

    try:
        app.run(host='0.0.0.0', port=8000, debug=True)
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass




