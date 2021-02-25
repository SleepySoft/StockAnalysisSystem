import requests
import datetime
import traceback
import pandas as pd
from functools import partial
import StockAnalysisSystem.core.Utility.JsonSerializerImpl
from StockAnalysisSystem.core.Utility.JsonSerializer import serialize, deserialize


class RestInterface:
    def __init__(self):
        self.__token = None
        self.__timeout = 9999   # Blocking in request for debug
        self.__api_url = 'http://127.0.0.1:80/api'

    def if_init(self, api_uri: str = None, token: str = None, timeout=None) -> bool:
        if token is not None:
            self.__token = token
        if timeout is not None:
            self.__timeout = timeout
        if api_uri is not None:
            self.__api_url = api_uri
        return True

    def if_prob(self) -> dict:
        return {
            'name': 'Rest Interface',
            'version': '1.0.0',
        }

    # ------------------------------------------------------------------------------------

    def __getattr__(self, attr):
        return partial(self.rest_interface_proxy, attr)

    def rest_interface_proxy(self, api: str, *args, **kwargs) -> any:
        """
        Cooperate with WebApiInterface.rest_interface_stub
        :param api: The function name of interface that you want to call
        :param args: The list args (which will be ignored in server side)
        :param kwargs: The key-value args
        :return: The response of server
        """
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
            return self.deserialize_response(resp.text) if (resp.text is not None and resp.text != '') else None
        except Exception as e:
            print('Parse result fail: ' + str(e))
            print(traceback.format_exc())
        finally:
            pass

    @staticmethod
    def deserialize_response(resp_text: str) -> any:
        result = deserialize(resp_text)
        return result


# ----------------------------------------------------------------------------------------------------------------------

def main():
    caller = RestInterface()
    caller.if_init(api_uri='http://127.0.0.1:80/api', token='xxxxxx')

    df = caller.sas_query('Market.SecuritiesInfo', '000001.SZSE')
    print(df)

    df = caller.sas_query('Finance.IncomeStatement', '000001.SZSE', ('2000-01-01', '2020-12-31'), readable=True)
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


