#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/09/04
@file: constant.py
@function:
@modify:
"""


AR_UNKNOWN = 0
AR_BALANCE_SHEET = 1
AR_INCOME_STATEMENT = 2
AR_CASHFLOW_STATEMENT = 3
ANNUAL_REPORT_ENUMS = [AR_BALANCE_SHEET, AR_INCOME_STATEMENT, AR_CASHFLOW_STATEMENT]
ANNUAL_REPORT_TYPES = ['balance_sheet', 'income_statement', 'cash_flow_statement']
REPORT_PERIOD_TYPES = ['annual', 'quarterly', 'monthly', 'other']


def annual_report_enum2type(e):
    switcher = {
        AR_BALANCE_SHEET: "balance_sheet",
        AR_INCOME_STATEMENT: "income_statement",
        AR_CASHFLOW_STATEMENT: "cash_flow_statement",
    }
    return switcher.get(e, "unknown")


def annual_report_type2enum(t):
    switcher = {
        "balance_sheet": AR_BALANCE_SHEET,
        "income_statement": AR_INCOME_STATEMENT,
        "cash_flow_statement": AR_CASHFLOW_STATEMENT,
    }
    return switcher.get(t, AR_UNKNOWN)
