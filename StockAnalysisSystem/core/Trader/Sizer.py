from .Interface import IMarket, ISizer, Position


class FullPositionBuy(ISizer):
    def __init__(self, security: str):
        super(FullPositionBuy, self).__init__(security)

    def amount(self, market: IMarket, position: Position) -> int:
        pass



