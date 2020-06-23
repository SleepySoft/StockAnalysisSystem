from StockAnalysisSystem.core.StockAnalysisSystem import StockAnalysisSystem
from StockAnalysisSystem.core.Utiltity.time_utility import *

from StockAnalysisSystem.core.Trader.Market import MarketBackTesting
from StockAnalysisSystem.core.Trader.TradeStrategy import Trader
from StockAnalysisSystem.core.Trader.Broker import Broker


sas = StockAnalysisSystem()
market = MarketBackTesting(sas.get_data_hub_entry(), text_auto_time('2019-01-01'), text_auto_time('2020-01-01'))
broker = Broker()
trader = Trader()

market.watch_security('000001.SZSE', broker)
market.watch_security('000001.SZSE', trader)
market.load_back_testing_data('000001.SZSE', True)
market.run()











