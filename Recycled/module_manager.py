#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/10
@file: module_manager.py
@function:
@modify:
"""
import os
import traceback

import Utiltity.common


class IPluginClass:
    def Name(self) -> str: pass
    def Depends(self) -> [str]: pass
    def SetEnvoriment(self, sAs): pass


def GetModuleClass() -> IPluginClass: pass


def ListObjFunction(obj, function_name: str) -> [str]:
    return [func for func in dir(obj) if callable(getattr(obj, func))]


def IsFunctionExists(obj, function_name: str) -> bool:
    try:
        return callable(getattr(obj, function_name))
    except Exception as e:
        print("Check callable fail.!")
        print('Error =>', e)
        return False
    finally:
        pass


class ModuleManager:

    class ModuleData:
        def __init__(self):
            self.Inst = None
            self.Class = None
            self.Module = None
            self.FileName = ''
            self.PluginName = ''

    def __init__(self):
        self.__modules = []
        pass

    def Init(self) -> bool:
        return True

    def GetModules(self) -> [ModuleData]:
        return self.__modules

    def PickupModules(self, module_names: [str]) -> []:
        return [m.Inst for m in self.__modules if m.PluginName in module_names]

    def LoadModuleFromFolder(self, folder: str) -> bool:
        self.__modules = self.__load_plugin(folder)
        return True

    @staticmethod
    def SortModules(modules: [IPluginClass]) -> [IPluginClass]:
        pre_sort_list = [(m.Name(), [d for d in m.Depends()]) for m in modules]
        sorted_list = Utiltity.common.topological_sort(pre_sort_list)
        sorted_module = []
        for name in sorted_list:
            for module in modules:
                if module.Name() == name:
                    sorted_module.append(module)
                    break
        return sorted_module

    def __load_plugin(self, module_path: str) -> ([str], []):
        module_data_list = []
        py_list, module_list = self.__load_plugin_module(module_path)
        for py, mdl in zip(py_list, module_list):
            class_, inst = self.__create_plugin_class(mdl)
            if inst is None:
                continue
            try:
                md = self.ModuleData()
                md.Inst = inst
                md.Module = mdl
                md.Class = class_
                md.FileName = py
                md.PluginName = inst.Name()
                module_data_list.append(md)
            except Exception as e:
                print("Create Plugin Class Fail!")
                print('Error =>', e)
                print('Error =>', traceback.format_exc())
            finally:
                pass
        return module_data_list

    def __load_plugin_module(self, module_path: str) -> ([str], []):
        py_list = []
        module_list = []
        module_files = os.listdir(module_path)
        for file_name in module_files:
            if not file_name.endswith(".py") or file_name.startswith("_"):
                continue
            plugin_name = os.path.splitext(file_name)[0]
            plugin = __import__(module_path + '.' + plugin_name, fromlist=[plugin_name])
            if not IsFunctionExists(plugin, 'GetModuleClass'):
                continue
            py_list.append(file_name)
            module_list.append(plugin)
        return py_list, module_list

    def __create_plugin_class(self, module) -> (type, object):
        import stock_analysis_system as sAs
        try:
            class_ = module.GetModuleClass()
            inst = class_()
            if self.__verify_plugin_class(inst):
                inst.SetEnvoriment(sAs.instance)
                return class_, inst
        except Exception as e:
            print("Create Plugin Class Fail!")
            print('Error =>', e)
            print('Error =>', traceback.format_exc())
        finally:
            pass
        return None, None

    @staticmethod
    def __verify_plugin_class(inst):
        try:
            return isinstance(inst.Name(), str) and isinstance(inst.Depends(), list)
        except Exception as e:
            print("Create Plugin Class Fail!")
            print('Error =>', e)
            print('Error =>', traceback.format_exc())
        finally:
            pass
        return False


