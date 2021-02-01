import json
import pandas as pd
from flask import request
from StockAnalysisSystem.interface.interface_local import LocalInterface, traceback
from StockAnalysisSystem.service.provider.provider import ServiceProvider
from StockAnalysisSystem.core.config import Config
import StockAnalysisSystem.core.Utiltity.JsonSerializerImpl
from StockAnalysisSystem.core.Utiltity.JsonSerializer import serialize, deserialize


# ----------------------------------------------------------------------------------------------------------------------

class WebApiInterface:
    def __init__(self, provider: ServiceProvider):
        self.__provider: ServiceProvider = provider

    def api_stub(self, req_args: dict) -> str:
        api = req_args.get('api', None)
        token = req_args.get('token', None)
        args_json = req_args.get('args', '')
        kwargs_json = req_args.get('kwargs', '')

        if self.check_request(api, token, args_json, kwargs_json):
            success, args, kwargs = self.parse_request(args_json, kwargs_json)
            return self.dispatch_request(api, token, *args, **kwargs)
        return ''

    def check_request(self, api: str, token: str, args_json: str, kwargs_json: str) -> bool:
        return isinstance(api, str) and api != '' and \
               isinstance(token, str) and token != '' and \
               isinstance(args_json, str) and isinstance(kwargs_json, str)

    def parse_request(self, args_json: str, kwargs_json: str) -> (bool, list, dict):
        try:
            args = deserialize(args_json)
            kwargs = deserialize(kwargs_json)
            return isinstance(args, list) and isinstance(kwargs, dict), args, kwargs
        except Exception as e:
            print(str(e))
            return False, [], {}
        finally:
            pass

    def dispatch_request(self, api: str, token: str, *args, **kwargs) -> any:
        # if api == 'query':
        #     df = self.__provider.query(*args, **kwargs, token=token)
        #     return '' if df is None else self.serialize_response(df)
        # else:
        resp = self.__provider.interface_call(token, api, *args, **kwargs)
        if resp is None:
            resp = self.__provider.sys_call(token, api, *args, **kwargs)
        resp_serialized = self.serialize_response(resp)
        return resp_serialized

    @staticmethod
    def serialize_response(resp) -> str:
        try:
            return serialize(resp) if resp is not None else ''
        except Exception as e:
            print('Serialize Response Fail: ' + str(e))
            print(traceback.format_exc())
            return ''
        finally:
            pass


# ----------------------------------------------------------------------------------------------------------------------

webapi_interface: WebApiInterface = None
service_provider: ServiceProvider = None


# ----------------------------------------------------------------------------------------------------------------------

def handle_request(flask_request: request) -> str:
    req_data = flask_request.data
    req_dict = json.loads(req_data)

    global webapi_interface
    return webapi_interface.api_stub(req_dict)


# ----------------------------------------------------------------------------------------------------------------------

def load_config(config: Config):
    pass


def init(provider: ServiceProvider, config: Config):
    global service_provider
    service_provider = provider

    global webapi_interface
    webapi_interface = WebApiInterface(provider)

    load_config(config)




