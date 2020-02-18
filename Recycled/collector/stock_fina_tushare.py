import tushare as ts
import config


class StockFinancialDataFromTuShare:
    def __init__(self):
        ts.set_token(config.TS_TOKEN)
        self.__pro = ts.pro_api()

    def init(self) -> bool:
        pass

    def inited(self) -> bool:
        pass

    # Validate this Collector is still valid or not.
    def validate(self) -> bool:
        pass

    # Fetch data from internet.
    def fetch_data(self, **kw) -> bool:
        pass

    # Auto check and update data to DB. Depends on collector's implementation.
    def check_update(self, **kw) -> bool:
        pass

    # Force update all data in DB.
    def force_update(self, **kw) -> bool:
        pass

