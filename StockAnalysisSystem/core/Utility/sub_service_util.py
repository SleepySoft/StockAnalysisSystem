import datetime


class ServiceEvent:
    TIMER_EVENT = 'timer_event'

    def __init__(self):
        self.__event_data = {}
        self.__post_timestamp = datetime.datetime.now()
        self.__process_timestamp = datetime.datetime.now()

    def event_class(self) -> str:
        pass

    # ---------------------------------------------------------------------

    def get_event_data(self, key: str) -> any:
        return self.__event_data.get(key, None)

    def set_event_data(self, key: str, val: any) -> any:
        self.__event_data[key] = val

    # ---------------------------------------------------------------------

    def get_post_timestamp(self) -> datetime.datetime:
        return self.__post_timestamp

    def get_process_timestamp(self) -> datetime.datetime:
        return self.__process_timestamp

    def update_post_timestamp(self):
        self.__post_timestamp = datetime.datetime.now()

    def update_process_timestamp(self):
        self.__process_timestamp = datetime.datetime.now()





