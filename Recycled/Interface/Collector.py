class Collector:
    def __init__(self):
        pass

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

    # # Force update all data in DB.
    # def force_update(self, **kw) -> bool:
    #     pass
    #
    # # Flush memory data to DB
    # def dump_to_db(self, **kw) -> bool:
    #     pass
    #
    # def load_from_db(self, **kw) -> bool:
    #     pass
    #
    # def dump_to_file(self, path: str, **kw) -> bool:
    #     pass
    #
    # def load_from_file(self, path: str, **kw) -> bool:
    #     pass


