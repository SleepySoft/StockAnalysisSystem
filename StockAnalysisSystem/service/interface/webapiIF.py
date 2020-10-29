import json
from ..provider.provider import ServiceProvider


class WebApiInterface:
    def __init__(self, provider: ServiceProvider):
        self.__provider = provider

    def api_stub(self, args: dict):
        api = args.get('api')
        token = args.get('token')
        params = args.get('params')

        return self.dispatch_request(api, token, params) if self.check_request(api, token, params) else ''

    def check_request(self, api, token, params) -> bool:
        return True

    def dispatch_request(self, api, token, params) -> any:
        return True

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




