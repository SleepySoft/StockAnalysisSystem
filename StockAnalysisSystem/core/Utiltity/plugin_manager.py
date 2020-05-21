import os
import traceback
from inspect import getmembers, isfunction


"""
A plug-in module should include following functions:
    plugin_prob() -> dict : Includes 'name', 'version', 'tags'
    plugin_capacities() -> [str] : Lists the capacity that module supports
"""


class PluginManager:
    def __init__(self, plugin_path: str = ''):
        self.__path = []
        self.__plugins = []
        if plugin_path != '':
            self.add_plugin_path(plugin_path)

    def add_plugin_path(self, plugin_path: str):
        self.__path.append(plugin_path)

    def refresh(self):
        """
        Refresh plugin list immediately. You should call this function if any updates to the plug-in folder.
        :return: None
        """
        all_plugin_list = []
        for plugin_path in self.__path:
            try:
                plugin_list = self.__load_from_single_path(plugin_path)
                all_plugin_list.extend(plugin_list)
            except Exception as e:
                print('Load plugin from path % Fail.', plugin_path)
                print(str(e))
                print('Ignore.')
            finally:
                pass
        self.__plugins = all_plugin_list

    def all_modules(self) -> list:
        return [plugin for file_name, plugin in self.__plugins]

    def find_module_has_capacity(self, capacity: str) -> [object]:
        """
        Finds the module that supports the specified feature.
        :param capacity: The capacity you want to check.
        :return: The module list that has this capacity.
        """
        module_list = []
        for file_name, plugin in self.__plugins:
            # capacities = self.__safe_execute(plugin, 'plugin_capacities')
            # if isinstance(capacities, list) and capacity in capacities:
            if self.__safe_execute(plugin, 'plugin_adapt', capacity):
                module_list.append(plugin)
        return module_list

    def check_module_has_function(self, module: object, function: str) -> bool:
        try:
            return callable(getattr(module, function))
        except Exception as e:
            print('Check callable: ' + str(e))
            return False
        finally:
            pass

    def get_module_functions(self, module: object) -> [str]:
        """
        Get function of a module.
        :param module: The module that you want to check. Not support list.
        :return: The function list of this module
        """
        # getmembers returns a list of (object_name, object_type) tuples.
        functions_list = [o for o in getmembers(module) if isfunction(o[1])]
        return functions_list

    def execute_module_function(self, modules: object or [object], function: str, parameters: dict,
                                end_if_success: bool = True) -> object or [object]:
        """
        Execute function of Module
        :param modules: The module that you want to execute its function. Can be an object or a list of object
        :param function: The function you want to invoke
        :param parameters: The parameter of the invoking function
        :param end_if_success: If True, this function will return at the first successful invoking.
        :return: The object that the invoking function returns, it will be a list if the modules param is a list.
                 Includes None return.
        """
        if not isinstance(modules, (list, tuple)):
            modules = [modules]
        result_list = []
        for module in modules:
            result_obj = self.__safe_execute(module, function, *(), **parameters)
            if result_obj is not None:
                result_list.append(result_obj)
                if end_if_success:
                    break
        return result_list

    # ---------------------------------------------------------------------------------------

    def __load_from_single_path(self, plugin_path) -> list:
        """
        Refresh plugin list immediately. You should call this function if any updates to the plug-in folder.
        :return: None
        """

        from os import sys
        sys.path.append(plugin_path)

        plugin_list = []
        module_files = os.listdir(plugin_path)

        for file_name in module_files:
            if not file_name.endswith('.py') or file_name.startswith('_') or file_name.startswith('.'):
                continue
            plugin_name = os.path.splitext(file_name)[0]
            try:
                plugin = __import__(plugin_name)
            except Exception as e:
                print('Error => When import module: ' + plugin_name)
                print('Error =>', e)
                print('Error =>', traceback.format_exc())
                print('Error => Ignore')
                continue
            finally:
                pass
            if not self.check_module_has_function(plugin, 'plugin_prob') or \
                    not self.check_module_has_function(plugin, 'plugin_capacities'):
                continue
            plugin_list.append((file_name, plugin))
        return plugin_list

    # --------------------------------------- Execute ---------------------------------------

    def __safe_execute(self, module: object, _function: str, *argc, **argv) -> object:
        try:
            func = getattr(module, _function)
            return_obj = func(*argc, **argv)
        except Exception as e:
            return_obj = None
            print("Function run fail.")
            print('Error =>', e)
            print('Error =>', traceback.format_exc())
        finally:
            pass
        return return_obj








