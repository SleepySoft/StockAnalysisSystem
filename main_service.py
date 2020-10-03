import hashlib
import traceback

from flask import Flask, request, make_response
import StockAnalysisSystem.webservice.route as web_route
import StockAnalysisSystem.wechatservice.route as wechat_route


# ----------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)


# ----------------------------------------------------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def root_entry():
    print('Hello')
    return 'Hello'


@app.route('/wx', methods=['GET', 'POST'])
def wechat_entry():
    response = wechat_route.handle_request(request)
    return response


# ----------------------------------------------------------------------------------------------------------------------

def main():
    web_route.init()
    wechat_route.init()
    app.run(host='0.0.0.0', port=80, debug=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass


