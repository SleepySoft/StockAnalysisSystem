import h5py
import numpy as np
import tushare as ts
import time
import datetime


pro = ts.pro_api('a54958861f0f432ced60b01e875240942463f3357e22f944223669fb')
market_data = pro.stock_basic(fields=['ts_code', 'symbol', 'name', 'list_date'])

f = h5py.File('test_h5py.h5', 'w')

count = 0
daily_data_sets = []
for ts_code, listing_date in zip(market_data['ts_code'], market_data['list_date']):
    ts_until = datetime.datetime.now().strftime('%Y%m%d')
    result_daily = pro.daily(ts_code=ts_code, start_date=listing_date, end_date=ts_until)

    if ts_code not in f.keys():
        stock_group = f.create_group(ts_code)
    else:
        stock_group = f[ts_code]

    for column in result_daily.columns:
        if column in ['ts_code']:
            continue

        s = result_daily[column]
        if column not in stock_group.keys():
            np_arr = s.to_numpy()
            print(np_arr.dtype)
            string_dt = h5py.special_dtype(vlen=str)
            stock_group.create_dataset(column, data=np_arr, chunks=True, compression='lzf')
        else:
            field = stock_group[column]
            # TODO: Append

        count += 1
        if count > 10:
            break
    time.sleep(0.1)

f.close()


