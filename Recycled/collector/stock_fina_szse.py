#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/09/18
@file: stock_fina_szse.py
@function:
@modify:
"""
import requests
import traceback
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

from Utiltity import common


class StockFinancialDataFromSZSE:

    def Name(self) -> str:
        return 'StockFinancialDataFromSZSE'
    def Depends(self) -> [str]:
        return []
    def SetEnvoriment(self, sAs):
        pass

    def FetchFinaReport(
            self, stock_code: str, report_period: str, extensions: [str],
            date_from: [str], date_to: [str], extra_param=None) -> pd.DataFrame:
        if report_period != 'annual' or 'pdf' not in extensions:
            return None
        year_from = common.str_to_date(date_from)
        year_to = common.str_to_date(date_to)
        year_from, year_to = common.correct_start_end(year_from, year_to)
        entry_page = self.__fetch_entry_page(stock_code, year_from, year_to)
        links = self.__parse_entry_page(entry_page)

        stock_list = []
        annual_list = []
        type_list = []
        content_list = []
        for annual in range(year_from, year_to):
            stock_list.append(stock_code)
            annual_list.append(annual)
            type_list.append('all')
            link = links.find(annual, '')
            if link != '':
                content = common.Download(link)
                content_list.append(content)
            else:
                content_list.append(None)

    def __fetch_entry_page(self, stock_code: str, year_start: int, year_end: int) -> str:
        current_year = datetime().year()
        # Only after 2001
        year_start = 2001 if year_start < 2001 else year_start
        year_start = current_year if year_start > current_year else year_start
        year_end = year_start if year_end < year_start else year_end
        year_end = current_year if year_end > current_year else year_end
        url = 'http://disclosure.szse.cn/m/search0425.jsp'
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'}
        payload = {
            'leftid': '1',
            'lmid': 'drgg',
            'pageNo': '1',
            'stockCode': stock_code,
            'keyword': '',
            'noticeType': '010301',
            'startTime': str(year_start) + '-01-01',
            'endTime': str(year_end) + '-09-01',
            'imageField.x': '23',
            'imageField.y': '8',
            'tzy': '',
        }
        try:
            r = requests.post(url, headers=headers, data=payload)
            return r.content.decode('gb2312')
        except Exception as e:
            print('Error =>', e)
            print('Error =>', traceback.format_exc())
            return ''
        finally:
            pass

    def TestWithFile(self, file_path: str):
        links = None
        with open(file_path, 'rt') as file:
            links = self.__parse_entry_page(file.read())
        if links is not None:
            print(links)

    # Return:
    #   Key: year; Value: URL
    def __parse_entry_page(self, entry_page: str) -> {int: str}:
        if entry_page == '':
            return None
        parse_list = []
        soup = BeautifulSoup(entry_page, "html.parser")
        common.ChainParse(soup, [
            ('table', {'width': '98%', 'align': 'right'}),
            ('tr', {}),
            ('td', {'align': 'left'}),
            ('a', {'target': 'new'})
        ], parse_list)
        return self.__parse_links(parse_list)

    def __parse_links(self, a_list) -> {int: str}:
        ret = {}
        for a in a_list:
            text = a.string
            link = a.attrs['href']
            if text is None or text == '' or link is None or link == '':
                continue
            if text.find('已取消') >= 0 or text.find('摘要') >= 0:
                continue
            token = text.find('年年度报告')
            if token < 4:
                continue
            year = text[token - 4:token]
            if year.isdigit():
                ret[int(year)] = 'http://disclosure.szse.cn/' + link
        return ret


        # tbody = table.find('tbody')
        # if tbody is None:
        #     return None
        # trs = tbody.findAll('tr')
        # for tr in trs:
        #     td = tr.find('td', {'align': 'left', 'class': 'td2'})
        #     if td is not None


