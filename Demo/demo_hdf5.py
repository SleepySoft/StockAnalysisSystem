import h5py
import sys
import traceback
import time
import datetime
import numpy as np
import pandas as pd
import tushare as ts


pro = ts.pro_api('a54958861f0f432ced60b01e875240942463f3357e22f944223669fb')


def save_hdf5(securities: [str], since: datetime.datetime, until: datetime.datetime):
    try:
        f = h5py.File('test_h5py.h5', 'a')
    except Exception as e:
        print('Open file for append fail, create instead.')
        f = h5py.File('test_h5py.h5', 'w')
    finally:
        pass

    for ts_code in securities:
        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')
        result_daily = pro.daily(ts_code=ts_code, start_date=ts_since, end_date=ts_until)

        del result_daily['ts_code']
        result_daily['trade_date'] = result_daily['trade_date'].apply(lambda x: int(x))

        start = time.time()
        print('Persist %s' % ts_code)

        if ts_code not in f.keys():
            stock_group = f.create_group(ts_code)
        else:
            stock_group = f[ts_code]
            if 'trade_date' in stock_group.keys():
                time_array = stock_group['trade_date'][:]
                time_field_max = time_array.max()
                result_daily = result_daily[result_daily['trade_date'] > time_field_max]
                if result_daily.empty:
                    print('No update.')
                    continue
            else:
                del stock_group[ts_code]
                stock_group = f.create_group(ts_code)

        for column in result_daily.columns:
            s = result_daily[column]
            np_arr = s.to_numpy()
            if column not in stock_group.keys():
                # https://stackoverflow.com/a/40312924/12929244
                if np_arr.dtype.kind == 'O':
                    string_dt = h5py.special_dtype(vlen=str)
                    stock_group.create_dataset(column, data=np_arr, dtype=string_dt,
                                               maxshape=(None,), chunks=True)
                else:
                    stock_group.create_dataset(column, data=np_arr,
                                               maxshape=(None,), chunks=True)
                print('Create dataset %s, length = %s' % (column, np_arr.shape[0]))
            else:
                append_len = np_arr.shape[0]
                exists_len = stock_group[column].shape[0]
                stock_group[column].resize((exists_len + append_len, ))
                stock_group[column][-append_len:] = np_arr
                print('Append dataset %s, length %s -> %s' % (column, exists_len, (exists_len + append_len)))

        print('Finish persistence %s, time spending: %sms' % (ts_code, 1000 * (time.time() - start)))
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
            # TODO:Error, length not equal
            stock_df[column] = np_arr
        print(stock_df)

        print('Finish loading %s, time spending: %sms' % (ts_code, 1000 * (time.time() - start)))
    f.close()


def main():
    market_data = pro.stock_basic(fields=['ts_code', 'symbol', 'name', 'list_date'])

    all_securities = list(market_data['ts_code'])
    update_securities = all_securities[:30]

    since = datetime.datetime(year=1990, month=1, day=1)
    while since < datetime.datetime.now():
        until = since + datetime.timedelta(days=10 * 365)
        save_hdf5(update_securities, since, until)
        since = until

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
