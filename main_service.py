import traceback

from flask import Flask, request
from StockAnalysisSystem.core.config import Config
import StockAnalysisSystem.service.interface.restIF as restIF
import StockAnalysisSystem.service.interface.wechatIF as wechatIF
import StockAnalysisSystem.service.interface.webapiIF as webapiIF
from StockAnalysisSystem.service.provider.provider import ServiceProvider


# ----------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)


# ----------------------------------------------------------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def root_entry():
    print('-> Request /')
    return ''


@app.route('/api', methods=['POST'])
def root_entry():
    return webapiIF.hand


@app.route('/analysis', methods=['GET', 'POST'])
def analysis_entry():
    print('-> Request /analysis')
    return restIF.analysis(request)


@app.route('/query', methods=['GET'])
def query_entry():
    return restIF.query(request)


@app.route('/wx', methods=['GET', 'POST'])
def wechat_entry():
    print('-> Request /wx')
    try:
        response = wechatIF.handle_request(request)
    except Exception as e:
        print('/wx Error', e)
        print(traceback.format_exc())
        response = ''
    finally:
        pass
    return response


# ----------------------------------------------------------------------------------------------------------------------

def init(provider: ServiceProvider, config: Config):
    config.load_config()
    provider.init(config)
    restIF.init(provider, config)
    wechatIF.init(provider, config)


def main():
    config = Config()
    provider = ServiceProvider({
        'stock_analysis_system': True,
        'offline_analysis_result': True,
    })
    init(provider, config)
    port = config.get('service_port', '80')
    debug = config.get('service_debug', 'true')
    print('Start service: port = %s, debug = %s.' % (port, debug))

    # https://stackoverflow.com/a/9476701/12929244
    app.run(host='0.0.0.0', port=str(port), debug=(debug == 'true'), use_reloader=False)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass


