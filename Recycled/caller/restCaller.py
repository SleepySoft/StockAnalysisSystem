import base64
import pickle
import traceback

import requests
import pandas as pd
import StockAnalysisSystem.core.Utility.time_utility as sasTimeUtil


class RestCaller:
    def __init__(self, service_url: str = 'http://127.0.0.1'):
        self.__service_url = service_url

    def query(self, uri: str, identity: str or [str] = None,
              time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        if not isinstance(uri, str):
            return None
        uri_arg = uri

        if isinstance(identity, str):
            identity_arg = identity
        elif isinstance(identity, (list, tuple, set)):
            identity_arg = ','.join(identity)
        elif identity is None:
            identity_arg = None
        else:
            return None

        if isinstance(time_serial, (list, tuple, set)):
            since_arg = sasTimeUtil.datetime2text(time_serial[0]) if len(time_serial) > 0 else None
            until_arg = sasTimeUtil.datetime2text(time_serial[1]) if len(time_serial) > 1 else None
        else:
            since_arg = None
            until_arg = None

        args = self.to_url_args(
            uri=uri_arg,
            identity=identity_arg,
            since=since_arg,
            until=until_arg,
        )

        r = requests.get(self.__service_url + '/query', params=args)
        print('Receive length: %s' % len(r.content))
        resp = r.content
        resp_str = resp.decode('utf-8')
        df = self.deserialize_dataframe(resp_str)
        return df

    # ------------------------------------------------------------------------------------------------------------------

    # https://stackoverflow.com/a/57930738/12929244

    @staticmethod
    def serialize_dataframe(df: pd.DataFrame) -> str:
        pickle_bytes = pickle.dumps(df)
        b64_pickle_bytes = base64.b64encode(pickle_bytes)
        b64_pickle_bytes_str = b64_pickle_bytes.decode('utf-8')
        return b64_pickle_bytes_str

    @staticmethod
    def deserialize_dataframe(b64_pickle_bytes_str: str) -> pd.DataFrame:
        pickle_bytes = base64.b64decode(b64_pickle_bytes_str)
        df = pickle.loads(pickle_bytes)
        return df

    @staticmethod
    def to_url_args(**kwargs) -> str:
        args = ''
        for k, v in kwargs.items():
            if v is not None:
                args += '%s=%s' % (k, str(v))
        return args


# ----------------------------------------------------------------------------------------------------------------------

def main():
    caller = RestCaller()
    df = caller.query('Market.SecuritiesInfo')
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















