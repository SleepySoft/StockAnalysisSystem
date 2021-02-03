import sys
import traceback


class Dependency:
    def __init__(self):
        self.__dependency_table = {}

    def add_dependence(self, item: str or [str], dependence: str or [str]):
        item = self.__make_list(item)
        dependence = self.__make_list(dependence)

        for i in item:
            if i not in self.__dependency_table.keys():
                self.__dependency_table[i] = dependence
            else:
                self.__dependency_table[i].extend(dependence)
        for d in dependence:
            if d not in self.__dependency_table.keys():
                self.__dependency_table[d] = []

    def sort_by_dependency(self) -> list:
        dependency_list = []
        dependency_table = self.__dependency_table.copy()

        while len(dependency_table) > 0:
            yield_list = self.__yield_independence_item(dependency_table)
            if len(yield_list) == 0:
                print('Circular dependence detected.')
                break
            dependency_list.extend(yield_list)
            self.__remove_item_from_key(dependency_table, yield_list)
            self.__remove_item_from_val(dependency_table, yield_list)
        return dependency_list

    # -----------------------------------------------------------------

    @staticmethod
    def __make_list(val: any) -> list:
        return val if isinstance(val, (list, tuple)) else [val]

    @staticmethod
    def __yield_independence_item(dependency_table: dict) -> list:
        yield_list = []
        for key in dependency_table.keys():
            if len(dependency_table[key]) == 0:
                yield_list.append(key)
        return yield_list

    @staticmethod
    def __remove_item_from_key(dependency_table: dict, yield_list: list):
        for key in yield_list:
            del dependency_table[key]

    @staticmethod
    def __remove_item_from_val(dependency_table: dict, yield_list: list):
        for key, val in dependency_table.items():
            dependency_table[key] = list(set(val) - set(yield_list))


# ----------------------------------------------------- Test Code ------------------------------------------------------


def test_basic():
    dependency = Dependency()
    dependency.add_dependence('A', ['B', 'E'])
    dependency.add_dependence('B', ['C', 'D'])
    dependency.add_dependence(['C', 'D'], 'G')
    dependency.add_dependence(['D', 'E'], 'F')
    dependency.add_dependence('G', 'H')
    dependency.add_dependence('F', ['I', 'K'])
    dependency.add_dependence('H', 'I')
    dependency.add_dependence('I', 'J')
    dependency_list = dependency.sort_by_dependency()
    print(dependency_list)

    dependency.add_dependence('J', 'A')
    dependency_list = dependency.sort_by_dependency()
    print(dependency_list)


def test_entry():
    test_basic()


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_entry()

    # If program reaches here, all test passed.
    print('All test passed.')


# ------------------------------------------------- Exception Handling -------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass


