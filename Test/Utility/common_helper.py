import datetime


class TestWrapper:
    LINE_LENGTH = 100

    def __init__(self, name: str):
        self.__test_name = name
        self.__test_start = datetime.datetime.now()

    def __enter__(self):
        self.print_in_splitter_mid('-', self.__test_name)
        self.__test_start = datetime.datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        time_str = 'Time spending: %s ms' % ((datetime.datetime.now() - self.__test_start).total_seconds() * 1000)
        self.print_in_splitter_mid(' ', time_str)
        print('')

    @staticmethod
    def print_in_splitter_mid(splitter:str, text: str):
        prefix = splitter * ((TestWrapper.LINE_LENGTH - 2 - len(text)) // 2)
        surfix = splitter * (TestWrapper.LINE_LENGTH - 2 - len(prefix) - len(text))
        print('%s %s %s' % (prefix, text, surfix))
