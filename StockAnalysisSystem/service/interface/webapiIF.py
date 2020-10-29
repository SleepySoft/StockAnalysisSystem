import json

import xmltodict
from flask import request
from ..provider.provider import ServiceProvider
from StockAnalysisSystem.core.config import Config

webapi_interface = None
service_provider: ServiceProvider = None

# ----------------------------------------------------------------------------------------------------------------------


class WebApiInterface:
    def __init__(self, provider: ServiceProvider):
        self.__provider = provider

    def api_stub(self, args: dict):
        api = args.get('api', None)
        token = args.get('token', None)
        params = args.get('params', {})

        return self.dispatch_request(api, token, params) \
            if self.check_request(api, token, params) else ''

    def check_request(self, api: str, token: str, params: dict) -> bool:
        return isinstance(api, str) and api != '' and \
               isinstance(token, str) and token != '' and \
               isinstance(params, dict)

    def dispatch_request(self, api: str, token: str, params: dict) -> any:
        if api == 'query':
            return self.__provider.query(**params)

    @staticmethod
    def serialize_response(**kwargs) -> str:
        try:
            return json.dumps(kwargs)
        except Exception as e:
            return ''
        finally:
            pass

    @staticmethod
    def deserialize_params(request_params: str) -> dict:
        try:
            return json.loads(request_params)
        except Exception as e:
            return {}
        finally:
            pass


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




