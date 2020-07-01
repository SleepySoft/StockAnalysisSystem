import os

import StockAnalysisSystem.api as sas_api
from StockAnalysisSystem.core.Utiltity.time_utility import *

from StockAnalysisSystem.core.Trader.Market import MarketBackTesting
from StockAnalysisSystem.core.Trader.TradeStrategy import *
from StockAnalysisSystem.core.Trader.Broker import Broker


project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sas_api.config_set('NOSQL_DB_HOST', 'localhost')
sas_api.config_set('NOSQL_DB_PORT', '27017')
sas_api.config_set('TS_TOKEN', 'xxxxxxxxxxxx')

if not sas_api.init(project_path, True):
    print('sas init fail.')
    print('\n'.join(sas_api.error_log()))
    quit(1)

market = MarketBackTesting(sas_api.get_data_hub_entry(), text_auto_time('2018-01-01'), text_auto_time('2020-01-01'))
broker = Broker(market)
trader = GridTrader(market, broker, '000001.SZSE', 7.0, 4.0, 5)

market.load_back_testing_data('000001.SZSE', True)
market.watch_security('000001.SZSE', broker)
market.watch_security('000001.SZSE', trader)
# market.run()
market.back_testing_entry()

print('Finally total position:\n' + str(broker.position().statistics(market)))










