import traceback

import requests
from functools import partial
from StockAnalysisSystem.core.Utiltity.JsonSerializer import serialize, deserialize


class WebApiCaller:
    def __init__(self, api_url: str):
        self.__token = None
        self.__timeout = 10
        self.__api_url = api_url

    def __getattr__(self, attr):
        return partial(self.api_proxy, attr)

    def update_token(self, token: str):
        self.__token = token

    def set_timeout(self, timeout: int):
        self.__timeout = timeout

    def set_api_url(self, api_url: str):
        self.__api_url = api_url

    def api_proxy(self, api: str, *args, **kwargs) -> any:
        payload = {
            'api': api,
            'token': self.__token,
            'args': serialize(args),
            'kwargs': serialize(kwargs),
        }
        headers = {

        }

        try:
            resp = requests.post(self.__api_url, json=payload, headers=headers, timeout=self.__timeout)
            return self.deserialize_response(resp.text)
        except Exception as e:
            print('Parse result fail: ' + str(e))
            print(traceback.format_exc())
        finally:
            pass

    @staticmethod
    def deserialize_response(resp_text: str) -> any:
        # result = json.loads(resp_text)
        result = deserialize(resp_text)
        return result


# ----------------------------------------------------------------------------------------------------------------------

def main():
    caller = WebApiCaller('http://127.0.0.1/api')
    caller.update_token('xxxxxx')

    df = caller.query('Market.SecuritiesInfo', '000001.SZSE')
    print(df)

    df = caller.query('Finance.IncomeStatement', '000001.SZSE', ('2000-01-01', '2020-12-31'), readable=True)
    print(df)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass


