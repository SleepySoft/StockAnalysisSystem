import datetime
from dataclasses import dataclass
from .constant import *


@dataclass
class BarData:
    """
    Candlestick bar data of a certain trading period.
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    extra: dict = None

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"




