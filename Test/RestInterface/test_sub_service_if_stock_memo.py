import traceback
from Test.Utility.common_helper import TestWrapper
from StockAnalysisSystem.interface.interface_rest import RestInterface


def main():
    caller = RestInterface()
    caller.if_init(api_uri='http://127.0.0.1:80/api', token='xxxxxx')

    with TestWrapper('get_stock_memo_all_security'):
        memo_securities = caller.get_stock_memo_all_security()
        print(memo_securities)

        with TestWrapper('stock_memo_get_record'):
            for s in memo_securities:
                df = caller.stock_memo_get_record(s)
                print(df)

    with TestWrapper('all_black_list'):
        black_list_securities = caller.all_black_list()
        print(black_list_securities)

    with TestWrapper('get_black_list_data'):
        df = caller.get_black_list_data()
        print(df)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass








