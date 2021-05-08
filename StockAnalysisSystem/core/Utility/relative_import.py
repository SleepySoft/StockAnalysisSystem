import os


class RelativeImport:
    def __init__(self, file_path: str):
        self.__root_path = os.path.dirname(os.path.abspath(file_path))

    def __enter__(self):
        if self.__root_path not in os.sys.path:
            os.sys.path.append(self.__root_path)
        else:
            self.__root_path = ''

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__root_path != '' and self.__root_path not in os.sys.path:
            os.sys.path.remove(self.__root_path)
