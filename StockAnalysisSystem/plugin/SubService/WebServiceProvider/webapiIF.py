import os
import json
import traceback
from flask import request
from StockAnalysisSystem.core.config import Config
from StockAnalysisSystem.core.Utility.relative_import import RelativeImport
from StockAnalysisSystem.core.Utility.JsonSerializer import serialize, deserialize
import StockAnalysisSystem.core.Utility.JsonSerializerImpl

with RelativeImport(__file__):
    from service_provider import ServiceProvider


# ----------------------------------------------------------------------------------------------------------------------

class WebApiInterface:
    def __init__(self, provider: ServiceProvider):
        self.__provider: ServiceProvider = provider

    def rest_interface_stub(self, req_args: dict) -> str:
        """
        Cooperate with RestInterface.rest_interface_proxy
        Check and dispatch the rest call to local interface
        :param req_args: The web request args
        :return: Web response
        """
        resp = ''
        api = req_args.get('api', None)
        print('==> ' + api)

        if self.is_special_api(api):
            resp = self.handle_special_api(api, req_args)
        else:
            token = req_args.get('token', None)
            args_json = req_args.get('args', '')
            kwargs_json = req_args.get('kwargs', '')

            if self.check_request(api, token, args_json, kwargs_json):
                success, args, kwargs = self.parse_request(args_json, kwargs_json)
                resp = self.dispatch_request(api, token, *args, **kwargs)
        print('<== ' + api)

        return resp

    def is_special_api(self, api: str) -> bool:
        return api in ['login', 'logoff']

    def handle_special_api(self, api: str, req_args: dict) -> str:
        args_json = req_args.get('args', '')
        kwargs_json = req_args.get('kwargs', '')
        success, args, kwargs = self.parse_request(args_json, kwargs_json)

        if api == 'login':
            token = self.__provider.login(kwargs.get('username', None), kwargs.get('password', None))
            return token
        elif api == 'logoff':
            token = req_args.get('token', '')
            self.__provider.logoff(token)

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
    return webapi_interface.rest_interface_stub(req_dict)


# ----------------------------------------------------------------------------------------------------------------------

def load_config(config: Config):
    pass


def init(provider: ServiceProvider, config: Config):
    global service_provider
    service_provider = provider

    global webapi_interface
    webapi_interface = WebApiInterface(provider)

    load_config(config)




