import hashlib
from flask import Flask, request, make_response
import StockAnalysisSystem.webservice.entry as web_entry
import StockAnalysisSystem.wechatservice.entry as wechat_entry


# ----------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)


# ----------------------------------------------------------------------------------------------------------------------

@app.route('/weixin', methods=['GET', 'POST'])
def wechat_entry():
    wechat_entry.handle_request(request)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    web_entry.init()
    wechat_entry.init()
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


