import hashlib
import traceback
from flask import Flask, request, make_response

from StockAnalysisSystem.core.config import Config
from StockAnalysisSystem.wechatservice.wechat_service import dispatch_wechat_message


app = Flask(__name__)


WECHAT_TOKEN = "xxxxxxx"


def load_config():
    global WECHAT_TOKEN
    config = Config()
    config.load_config()
    WECHAT_TOKEN = config.get('wechat_token')
    if WECHAT_TOKEN == '':
        print('Warning: Wechat token is empty.')


@app.route('/weixin', methods=['GET', 'POST'])
def wechat_entry():
    args = request.args

    signature = args.get('signature')
    timestamp = args.get('timestamp')
    nonce = args.get('nonce')
    echostr = args.get('echostr')

    # 1. 将token、timestamp、nonce三个参数进行字典序排序
    sign_arr = [WECHAT_TOKEN, timestamp, nonce]
    sign_arr.sort()
    sign_str = ''.join(sign_arr)

    # 2. 将三个参数字符串拼接成一个字符串进行sha1加密
    sign_dig = hashlib.sha1(sign_str).hexdigest()

    # 3. 开发者获得加密后的字符串可与signature对比
    if sign_dig == signature:
        # 根据请求方式.返回不同的内容 ,如果是get方式,代表是验证服务器有效性
        if request.method == 'GET':
            return echostr
        # 如果POST方式,代表是微服务器转发给我们的消息
        elif request.method == 'POST':
            return dispatch_wechat_message(request)
    else:
        return 'errno', 403


def main():
    load_config()
    app.run(host='0.0.0.0', port=8000, debug=True)


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8000, debug=True)
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass


