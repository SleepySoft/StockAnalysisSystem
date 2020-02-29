from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import stock_analysis_system
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Analyzer.AnalyzerUtility import *
except Exception as e:
    sys.path.append(root_path)

    import stock_analysis_system
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Analyzer.AnalyzerUtility import *
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------


def test_entry() -> bool:
    ret = True
    sas = stock_analysis_system.StockAnalysisSystem()
    if not sas.check_initialize():
        print('StockAnalysisSystem init fail.')
        print(sas.get_log_errors())
        return False

    data_hub = sas.get_data_hub_entry()
    se = sas.get_strategy_entry()

    # stock_list = data_hub.get_data_utility().get_stock_list()
    # stock_ids = [_id for _id, _name in stock_list]
    # stock_ids = ['600518.SSE']
    stock_ids = ['000004.SZSE']

    clock = Clock()

    result = se.run_strategy(stock_ids, [
        # '7a2c2ce7-9060-4c1c-bca7-71ca12e92b09',
        # 'e639a8f1-f2f5-4d48-a348-ad12508b0dbb',
        # 'f39f14d6-b417-4a6e-bd2c-74824a154fc0',
        # '3b01999c-3837-11ea-b851-27d2aa2d4e7d',
        # '1fdee036-c7c1-4876-912a-8ce1d7dd978b',

        # 'b0e34011-c5bf-4ac3-b6a4-c15e5ea150a6',
        # 'd811ebd6-ee28-4d2f-b7e0-79ce0ecde7f7',
        # '2c05bb4c-935e-4be7-9c04-ae12720cd757',
        # 'e6ab71a9-0c9f-4500-b2db-d682af567f70',
        # '4ccedeea-b731-4b97-9681-d804838e351b',

        'e515bd4b-db4f-49e2-ac55-1927a28d2a1c',
    ])

    # Dummy analyzers for test
    # result = se.run_strategy(stock_ids, [
    #     '5d19927a-2ab1-11ea-aee4-eb8a702e7495',
    #     'bc74b6fa-2ab1-11ea-8b94-03e35eea3ca4',
    #     '6b23435c-2ab1-11ea-99a8-3f957097f4c9',
    #     'd0b619ba-2ab1-11ea-ac32-43e650aafd4f',
    #     '78ffae34-2ab1-11ea-88ff-634c407b44d3',
    #     'd905cdea-2ab1-11ea-9e79-ff65d4808d88',
    # ])

    print('Analysis time spending: ' + str(clock.elapsed_s()) + ' s')

    passed_securities = pick_up_pass_securities(result, 50)
    print('Passed securities' + str(passed_securities))

    clock.reset()
    name_dict = sas.get_strategy_entry().strategy_name_dict()
    generate_analysis_report(result, 'analysis_report.xlsx', name_dict)
    print('Generate report time spending: ' + str(clock.elapsed_s()) + ' s')

    return ret


def main():
    test_entry()
    print('All Test Passed.')


# ----------------------------------------------------------------------------------------------------------------------

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






















