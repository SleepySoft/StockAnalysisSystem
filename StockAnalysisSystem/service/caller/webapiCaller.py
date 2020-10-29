import json
import requests
from functools import partial


class WebApiCaller:
    def __init__(self, api_url: str):
        self.__token = None
        self.__timeout = 10
        self.__api_url = api_url

    def __getattr__(self, attr):
        return partial(self.api_proxy, attr)

    def set_token(self, token: str):
        self.__token = token

    def set_timeout(self, timeout: int):
        self.__timeout = timeout

    def set_api_url(self, api_url: str):
        self.__api_url = api_url

    def api_proxy(self, api: str, **kwargs) -> any:
        payload = {
            'api': api,
            'token': self.__token,
            'params': self.serialize_params(**kwargs),
        }
        headers = {

        }

        try:
            resp = requests.post(self.__api_url, data=payload, headers=headers, timeout=self.__timeout)
            return self.deserialize_response(resp.text)
        except Exception as e:
            return None
        finally:
            pass

    @staticmethod
    def serialize_params(**kwargs) -> str:
        return json.dumps(kwargs)

    @staticmethod
    def deserialize_response(resp_text: str) -> any:
        result = json.loads(resp_text)
        return result


