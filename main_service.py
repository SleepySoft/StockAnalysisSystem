import hashlib
import traceback

from flask import Flask, request, make_response
import StockAnalysisSystem.webservice.entry as web_entry
import StockAnalysisSystem.wechatservice.entry as wechat_entry


# ----------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)


# ----------------------------------------------------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def root_entry():
    print('Hello')


@app.route('/weixin', methods=['GET', 'POST'])
def wechat_entry():
    wechat_entry.handle_request(request)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    web_entry.init()
    wechat_entry.init()
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


