import traceback
from functools import partial


class SysCall:

    # class Entry:
    #     def __init__(self, func_name: str, func_entry, **kwargs):
    #         self.__func_name = func_name
    #         self.__func_entry = func_entry
    #         self.__extra_data = kwargs
    #
    #     def get_data(self, key: str) -> any:
    #         return self.__extra_data.get(key)
    #
    #     def set_data(self, key: str, val: any):
    #         self.__extra_data[key] = val

    def __init__(self):
        # {name, (function_entry, property_dict)}
        self.__sys_call_table = {}

    def __getattr__(self, attr):
        return partial(self.sys_call, attr)

    def sys_call(self, func_name: str, *args, **kwargs) -> any:
        func, prop = self.__sys_call_table.get(func_name, (None, {}))
        if func is None:
            print('Warning: No sys call named: ' + func_name)
            return None
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())
            return None
        finally:
            pass

    def register_sys_call(self, func_name: str, func_entry, replace: bool = False, **kwargs) -> bool:
        """
        Register a sys-call.
        :param func_name: The function name that will be used for calling this function
        :param func_entry: The function. Should be callable.
        :param replace: Replace exists function if True else Ignore
        :param kwargs: Extra properties. Standard properties:
                        'group' as str: The group of this function
                        'document' as str: The document and description of this function
                        'parameters' as [(param_name, param_comments)]: The document of parameters by order
        :return:
        """
        if func_name in self.__sys_call_table.keys():
            if replace:
                print('Sys call [%s] already exists - replace.' % func_name)
            else:
                print('Sys call [%s] already exists - ignore.' % func_name)
                return False
        self.__sys_call_table[func_name] = (func_entry, kwargs)
        return True

    def unregister_sys_call(self, func_name: str):
        if func_name in self.__sys_call_table.keys():
            del self.__sys_call_table[func_name]

    # ----------------------------- Group -----------------------------

    def get_sys_call_by_group(self, group_name: str) -> [str]:
        return self.find_sys_call_by_property(group_name)

    def unregister_sys_call_by_group(self, group_name: str):
        self.unregister_sys_call_by_property('group', group_name)

    # ---------------------------- Common -----------------------------

    def has_sys_call(self, func_name: str) -> bool:
        func, _ = self.__sys_call_table.get(func_name, (None, {}))
        return func is not None

    def get_sys_call_property(self, func_name: str, k: str) -> any:
        _, prop = self.__sys_call_table.get(func_name, (None, {}))
        return prop.get(k, None)

    def find_sys_call_by_property(self, k: str, v: str) -> [str]:
        sys_call_names = []
        for func_name in self.__sys_call_table.keys():
            prop = self.__sys_call_table.get(func_name)
            if prop.get(k, None) == v:
                sys_call_names.append(func_name)
        return sys_call_names

    def unregister_sys_call_by_property(self, k: str, v: str):
        function_names = self.find_sys_call_by_property(k, v)
        for func_name in function_names:
            del self.__sys_call_table[func_name]

