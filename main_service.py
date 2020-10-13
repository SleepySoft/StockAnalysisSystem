import hashlib
import traceback

from flask import Flask, request, make_response
from StockAnalysisSystem.core.config import Config
import StockAnalysisSystem.webservice.route as web_route
import StockAnalysisSystem.wechatservice.route as wechat_route


# ----------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)


# ----------------------------------------------------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def root_entry():
    print('-> Request /')
    return ''


@app.route('/analysis', methods=['GET', 'POST'])
def analysis_entry():
    print('-> Request /analysis')
    return web_route.analysis(request)


@app.route('/wx', methods=['GET', 'POST'])
def wechat_entry():
    print('-> Request /wx')
    try:
        response = wechat_route.handle_request(request)
    except Exception as e:
        print('/wx Error', e)
        print(traceback.format_exc())
        response = ''
    finally:
        pass
    return response


# ----------------------------------------------------------------------------------------------------------------------

def init(config: Config):
    config.load_config()
    web_route.init(config)
    wechat_route.init(config)


def main():
    config = Config()
    init(config)
    port = config.get('service_port', '80')
    debug = config.get('service_debug', 'true')
    print('Start service: port = %s, debug = %s.' % (port, debug))
    app.run(host='0.0.0.0', port=str(port), debug=(debug == 'true'))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass


