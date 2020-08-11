import h5py
import sys
import traceback
import time
import datetime
import numpy as np
import pandas as pd
import tushare as ts


def save_hdf5():
    pro = ts.pro_api('a54958861f0f432ced60b01e875240942463f3357e22f944223669fb')
    market_data = pro.stock_basic(fields=['ts_code', 'symbol', 'name', 'list_date'])

    f = h5py.File('test_h5py.h5', 'w')

    count = 0
    for ts_code, listing_date in zip(market_data['ts_code'], market_data['list_date']):
        ts_until = datetime.datetime.now().strftime('%Y%m%d')
        result_daily = pro.daily(ts_code=ts_code, start_date=listing_date, end_date=ts_until)

        if ts_code not in f.keys():
            stock_group = f.create_group(ts_code)
        else:
            stock_group = f[ts_code]

        start = time.time()
        print('Persist %s' % ts_code)

        for column in result_daily.columns:
            if column in ['ts_code']:
                continue

            s = result_daily[column]
            if column not in stock_group.keys():
                np_arr = s.to_numpy()

                # https://stackoverflow.com/a/40312924/12929244
                if np_arr.dtype.kind == 'O':
                    string_dt = h5py.special_dtype(vlen=str)
                    stock_group.create_dataset(column, data=np_arr, dtype=string_dt, chunks=True, compression='lzf')
                else:
                    stock_group.create_dataset(column, data=np_arr, chunks=True, compression='lzf')
            else:
                field = stock_group[column]
                # TODO: Append

        print('Finish persistence %s, time spending: %sms' % (ts_code, 1000 * (time.time() - start)))

        count += 1
        if count > 10:
            break
        time.sleep(0.1)

    f.close()


def load_hdf5():
    f = h5py.File('test_h5py.h5', 'r')
    for ts_code in f.keys():
        start = time.time()
        print('Load %s' % ts_code)

        stock_df = pd.DataFrame()
        stock_group = f[ts_code]
        for column in stock_group.keys():
            np_arr = stock_group[column]
            stock_df[column] = np_arr
        print(stock_df)

        print('Finish loading %s, time spending: %sms' % (ts_code, 1000 * (time.time() - start)))
    f.close()


def main():
    save_hdf5()
    load_hdf5()
    print('Process Quit.')


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
