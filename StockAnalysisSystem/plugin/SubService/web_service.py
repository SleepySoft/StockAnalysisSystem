import os
import logging
import traceback
from flask import Flask, request

from StockAnalysisSystem.core.SubServiceManager import SubServiceContext
from StockAnalysisSystem.core.Utility.relative_import import RelativeImport

with RelativeImport(__file__):
    import WebServiceProvider.restIF as restIF
    import WebServiceProvider.webapiIF as webapiIF
    import WebServiceProvider.wechatIF as wechatIF
    from WebServiceProvider.service_provider import ServiceProvider


SERVICE_ID = 'f54e8afa-959d-44a2-8a95-545175be92a7'

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': SERVICE_ID,
        'plugin_name': 'WebService',
        'plugin_version': '0.0.0.1',
        'tags': ['Web', 'Flask', 'Http', 'Sleepy'],
    }


def plugin_adapt(service: str) -> bool:
    return service == SERVICE_ID


def plugin_capacities() -> list:
    return [
        'thread',         # SubService manager will create a thread for this service
    ]


# ----------------------------------------------------------------------------------------------------------------------

flaskApp: Flask = None
serviceProvider = ServiceProvider()
subServiceContext: SubServiceContext = None


def init(sub_service_context: SubServiceContext) -> bool:
    """
    System will invoke this function before startup() once. The initialization order of service is uncertain.
    :param sub_service_context: The instance of SubServiceContext
    :return: True if successful else False
    """
    try:
        global subServiceContext
        subServiceContext = sub_service_context

        serviceProvider.check_init(subServiceContext.sas_if,
                                   subServiceContext.sas_api)
        if not serviceProvider.is_inited():
            return False

        global flaskApp
        flaskApp = Flask(__name__)

        flaskApp.logger.setLevel(logging.ERROR)

        config = subServiceContext.sas_api.config()
        restIF.init(serviceProvider, config)
        webapiIF.init(serviceProvider, config)
        wechatIF.init(serviceProvider, config)
    except Exception as e:
        import traceback
        print('Plugin-in init error: ' + str(e))
        print(traceback.format_exc())
        return False
    finally:
        pass
    return True


def startup() -> bool:
    if flaskApp is None:
        return False

    @flaskApp.route('/', methods=['GET', 'POST'])
    def root_entry():
        print('-> Request /')
        return ''

    @flaskApp.route('/api', methods=['POST'])
    def webapi_entry():
        # print('-> Request /api')
        try:
            response = webapiIF.handle_request(request)
        except Exception as e:
            print('/api Error', e)
            print(traceback.format_exc())
            response = ''
        finally:
            pass
        return response

    @flaskApp.route('/analysis', methods=['GET', 'POST'])
    def analysis_entry():
        print('-> Request /analysis')
        return restIF.analysis(request)

    # @flaskApp.route('/query', methods=['GET'])
    # def query_entry():
    #     print('-> Request /query')
    #     try:
    #         response = restIF.query(request)
    #     except Exception as e:
    #         print('/wx Error', e)
    #         print(traceback.format_exc())
    #         response = ''
    #     finally:
    #         pass
    #     return response

    @flaskApp.route('/wx', methods=['GET', 'POST'])
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

    return True


def thread(context: dict):
    if flaskApp is not None:
        config = subServiceContext.sas_api.config()
        port = config.get('service_port', '80')
        debug = config.get('service_debug', 'true')
        print('Start service: port = %s, debug = %s.' % (port, debug))
        # https://stackoverflow.com/a/9476701/12929244
        flaskApp.run(host='0.0.0.0', port=str(port), debug=(debug == 'true'), use_reloader=False)

