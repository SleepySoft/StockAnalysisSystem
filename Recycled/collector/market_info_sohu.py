#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:YuQiu
@time: 2017/08/10
@file: market_info_sohu.py
@function:
@modify:
"""

import pandas as pd
import Utiltity.common


class MarketInformationFromSohu:

    def Name(self) -> str:
        return 'MarketInformationFromSohu'
    def Depends(self) -> [str]:
        return []
    def SetEnvoriment(self, sAs):
        pass

    # Columns: Name|Code
    # From 'http://q.stock.sohu.com/cn/zs.shtml' ->
    #      'http://hq.stock.sohu.com/zs/zs-2.html'
    def FetchIndexIntroduction(self, extra_param=None) -> pd.DataFrame:
        content_text = Utiltity.common.DownloadText('http://hq.stock.sohu.com/zs/zs-2.html')
        try:
            pos_start = content_text.find('<script>PEAK_ODIA')
            if pos_start < 0:
                print('Cannot find the specified token.')
                return None
            pos_start = content_text.find('(', pos_start)
            pos_end = content_text.find('</script>', pos_start)

            if pos_start < 0 or pos_end < 0:
                print('Cannot find parents.')
                return None

            content = content_text[pos_start + 1 : pos_end - 1]
            content = content.replace('\'indexlist\',', '')
            content = content.replace('\'', '"')

            df = pd.read_json(content)
            df.columns = ['Code', 'Name', 'price', 'change_amount', 'change_percent',
                          'current_trade', 'total_trade', 'amount', 'swap_rate', 'low',
                          'high', 'today_open', 'yesterday_close', 'link']
            df['Code'] = df['Code'].map(lambda x: x.replace('zs_', ''))
        except Exception as e:
            print(e)
            return None
        finally:
            pass
        return df


def GetModuleClass() -> object:
    return MarketInformationFromSohu
