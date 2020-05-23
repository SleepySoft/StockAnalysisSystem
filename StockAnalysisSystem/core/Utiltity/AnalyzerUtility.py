import openpyxl
import pandas as pd

from .common import *
from .df_utility import *
from ..DataHubEntry import DataHubEntry
from ..Database.DatabaseEntry import DatabaseEntry


def methods_from_prob(prob: dict) -> []:
    return methods_from_method_list(prob.get('methods', []))


def methods_from_method_list(method_list: list) -> []:
    return [method for method, _, _, _ in method_list]


# def standard_dispatch_analysis(securities: [str], methods: [str], data_hub, database,
#                                method_list: list) -> []:
#     result_list = []
#     for query_method in methods:
#         for hash_id, _, _, function_entry in method_list:
#             if hash_id == query_method:
#                 if function_entry is None:
#                     print('Method ' + hash_id + ' not implemented yet.')
#                 else:
#                     try:
#                         result = function_entry(securities, data_hub, database)
#                     except Exception as e:
#                         print('Execute analyzer [' + hash_id + '] Error: ')
#                         print(e)
#                         print(traceback.format_exc())
#                         result = None
#                     finally:
#                         pass
#                     if result is not None and len(result) > 0:
#                         result_list.append((query_method, result))
#                 break
#     return result_list


# ----------------------------------------------------------------------------------------------------------------------

class AnalysisResult:

    SCORE_MIN = 0
    SCORE_MAX = 100
    SCORE_PASS = SCORE_MAX
    SCORE_FAIL = SCORE_MIN
    SCORE_NOT_APPLIED = None

    WEIGHT_NORMAL = 1
    WEIGHT_ONE_VOTE_VETO = 999999

    def __init__(self, securities: str, score: int or bool, reason: str or [str] = '', weight: int = WEIGHT_NORMAL):
        self.method = ''
        self.securities = securities

        if isinstance(score, bool):
            self.score = AnalysisResult.SCORE_PASS if score else AnalysisResult.SCORE_FAIL
        elif isinstance(score, (int, float)):
            self.score = score
            self.score = min(self.score, AnalysisResult.SCORE_MAX)
            self.score = max(self.score, AnalysisResult.SCORE_MIN)
        else:
            self.score = score

        if reason is None:
            self.reason = ''
        elif isinstance(reason, (list, tuple)):
            self.reason = '\n'.join(reason)
        else:
            self.reason = reason

        self.weight = weight


# ----------------------------------------------------------------------------------------------------------------------

class AnalysisContext:
    def __init__(self):
        self.cache = {}
        self.extra = {}
        self.logger = None
        self.progress = None


# ----------------------------------------------------------------------------------------------------------------------

def function_entry_example(securities: str, data_hub, database, context: AnalysisContext) -> AnalysisResult:
    """
    The example of analyzer function entry.
    :param securities: A single securities code, should be a str.
    :param data_hub:  DataHubEntry type
    :param database: DatabaseEntry type
    :param context: AnalysisContext type, which can hold cache data for multiple analysis
    :return: AnalysisResult
    """
    pass


method_list_example = [
    ('5c496d06-9961-4157-8d3e-a90683d6d32c', 'analyzer brief', 'analyzer details', function_entry_example),
]


def standard_dispatch_analysis(securities: [str], methods: [str], data_hub, database,
                               extra: dict, method_list: list) -> [(str, [])] or None:
    context = AnalysisContext()
    if isinstance(extra, dict):
        context.extra = extra
        context.logger = extra.get('logger', print)
        context.progress = extra.get('progress', ProgressRate())

    result_list = []
    for query_method in methods:
        sub_list = []
        context.cache.clear()
        for hash_id, _, _, function_entry in method_list:
            if hash_id != query_method:
                continue
            if function_entry is None:
                print('Method ' + hash_id + ' not implemented yet.')
                break
            context.progress.set_progress(hash_id, 0, len(securities))
            for s in securities:
                try:
                    result = function_entry(s, data_hub, database, context)
                except Exception as e:
                    error_info = 'Execute analyzer [' + hash_id + '] for [' + s + '] got exception.'
                    print(error_info)
                    print(e)
                    print(traceback.format_exc())
                    result = AnalysisResult(s, AnalysisResult.SCORE_NOT_APPLIED, error_info)
                finally:
                    context.progress.increase_progress(hash_id)
                    print('Analyzer %s progress: %.2f%%' % (hash_id, context.progress.get_progress_rate(hash_id) * 100))
                if result is None:
                    result = AnalysisResult(s, AnalysisResult.SCORE_NOT_APPLIED, 'NONE')
                sub_list.append(result)

            # Fill result list for alignment
            while len(sub_list) < len(securities):
                sub_list.append(AnalysisResult(securities[len(sub_list)], AnalysisResult.SCORE_NOT_APPLIED, 'NONE'))
            result_list.append((query_method, sub_list))
            context.progress.set_progress(hash_id, len(securities), len(securities))
            break
    return result_list if len(result_list) > 0 else None


# --------------------------------------------------- Analyzer Helper --------------------------------------------------

# def check_append_report_when_data_missing(df: pd.DataFrame, securities: str,
#                                           uri: str, fields: str or [str], result: list):
#     if df is None or len(df) == 0:
#         error_info = uri + ': Cannot find data for securities : ' + securities
#         log_error(error_info)
#         result.append(AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, error_info))
#         return True
#     if not isinstance(fields, (list, tuple)):
#         fields = [fields]
#     for field in fields:
#         if field not in df.columns:
#             error_info = uri + ': Field ' + field + ' missing for securities : ' + securities
#             log_error(error_info)
#             result.append(AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, error_info))
#             return True
#     return False


def check_gen_report_when_data_missing(df: pd.DataFrame, securities: str,
                                       uri: str, fields: str or [str]) -> AnalysisResult or None:
    if df is None or len(df) == 0:
        error_info = uri + ': Cannot find data for securities : ' + securities
        log_error(error_info)
        return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, error_info)
    if not isinstance(fields, (list, tuple)):
        fields = [fields]
    for field in fields:
        if field not in df.columns:
            error_info = uri + ': Field ' + field + ' missing for securities : ' + securities
            log_error(error_info)
            return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, error_info)
    return None


def gen_report_when_analyzing_error(securities: str, exception: Exception):
    error_info = 'Error when analysing  : ' + securities + '\n'
    error_info += str(exception)
    log_error(error_info)
    print(traceback.format_exc())
    return AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, error_info)


def batch_query_readable_annual_report_pattern(
        data_hub, securities: str, time_serial: tuple,
        fields_balance_sheet: [str] = None,
        fields_income_statement: [str] = None,
        fields_cash_flow_statement: [str] = None) -> (pd.DataFrame, AnalysisResult):

    df = None
    if fields_balance_sheet is not None and len(fields_balance_sheet) > 0:
        df_balance, result = query_readable_annual_report_pattern(
            data_hub, 'Finance.BalanceSheet', securities, time_serial, fields_balance_sheet)
        if result is not None:
            return df, result
        df = df_balance

    if fields_income_statement is not None and len(fields_income_statement) > 0:
        df_income, result = query_readable_annual_report_pattern(
            data_hub, 'Finance.IncomeStatement', securities, time_serial, fields_income_statement)
        if result is not None:
            return df, result
        df = df_income if df is None else (pd.merge(df, df_income, how='left', on=['stock_identity', 'period']))

    if fields_cash_flow_statement is not None and len(fields_cash_flow_statement) > 0:
        df_cash, result = query_readable_annual_report_pattern(
            data_hub, 'Finance.CashFlowStatement', securities, time_serial, fields_cash_flow_statement)
        if result is not None:
            return df, result
        df = df_cash if df is None else (pd.merge(df, df_cash, how='left', on=['stock_identity', 'period']))
    df = df.sort_values('period')
    return df, None


def query_readable_annual_report_pattern(data_hub, uri: str, securities: str, time_serial: tuple,
                                         fields: [str]) -> (pd.DataFrame, AnalysisResult):
    """
    The pattern of query readable annual report. It will do the following things:
    1. Check readable names are all known
    2. Query data from data center
    3. Only keep annual report
    4. Check empty
    5. Fill na with 0.0 and sort by date
    :param data_hub: The instance of DataHubEntry
    :param uri: The uri user queries for
    :param securities: The securities user queries
    :param time_serial: The data range user queries
    :param fields: The readable fields user queries
    :return: (Query Result if successful, else None, Analysis Result if fail else None)
    """
    if not data_hub.get_data_center().check_readable_name(fields):
        return None, AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED, 'Unknown readable name detect.')

    fields_stripped = list(set(fields + ['stock_identity', 'period']))
    df = data_hub.get_data_center().query(uri, securities, time_serial, fields=fields_stripped, readable=True)
    if df is None or len(df) == 0:
        return None, AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED,
                                    'No data, skipped' + str(time_serial))

    # Only analysis annual report
    df = df[df['period'].dt.month == 12]

    if len(df) == 0:
        return None, AnalysisResult(securities, AnalysisResult.SCORE_NOT_APPLIED,
                                    'No data in this period' + str(time_serial))
    df.fillna(0.0, inplace=True)
    df = df.sort_values('period', ascending=False)

    return df, None


def check_industry_in(securities: str, industries: [str], data_hub: DataHubEntry,
                      database: DatabaseEntry, context: AnalysisContext) -> bool:
    nop(database)

    if context.cache.get('securities_info', None) is None:
        context.cache['securities_info'] = data_hub.get_data_center().query('Market.SecuritiesInfo')
    df_info = context.cache.get('securities_info', None)

    df_slice = df_info[df_info['stock_identity'] == securities]
    industry = get_dataframe_slice_item(df_slice, 'industry', 0, '')

    return industry in industries


# ---------------------------------------------------- Parse Result ----------------------------------------------------

"""
The results should look like:

method1           method2           method3           ...           methodM
m1_result1        m2_result1        m3_result1                      mM_result1
m1_result2        m2_result2        m3_result2                      mM_result2
m1_result3        m2_result3        m3_result3                      mM_result3
.                 .                 .                               .
.                 .                 .                               .
.                 .                 .                               .
m1_resultN        m2_resultN        m3_resultN                      mM_resultN
"""


def get_securities_in_result(result: dict) -> [str]:
    securities = []
    for method, results in result.items():
        for r in results:
            if str_available(r.securities) and r.securities not in securities:
                securities.append(r.securities)
    return securities


def pick_up_pass_securities(result: dict, score_threshold: int, not_applied_as_fail: bool = False) -> [str]:
    securities = get_securities_in_result(result)
    for method, results in result.items():
        for r in results:
            if r.score == AnalysisResult.SCORE_NOT_APPLIED:
                exclude = not_applied_as_fail
            else:
                exclude = (r.score < score_threshold)
            if exclude and r.securities in securities:
                securities.remove(r.securities)
    return securities


# ---------------------------------------------------- Excel Report ----------------------------------------------------


fill_pass = openpyxl.styles.PatternFill(patternType="solid", start_color="10EF10")
fill_flaw = openpyxl.styles.PatternFill(patternType="solid", start_color="FFFF10")
fill_fail = openpyxl.styles.PatternFill(patternType="solid", start_color="EF1010")
fill_none = openpyxl.styles.PatternFill(patternType="solid", start_color="808080")


def __score_to_fill_style(score: int or None):
    if score is None:
        fill_style = fill_none
    elif score < 50:
        fill_style = fill_fail
    elif score <= 75:
        fill_style = fill_flaw
    else:
        fill_style = fill_pass
    return fill_style


def __score_to_fill_text(score: int or None):
    if score is None:
        return '-'
    elif score == 0:
        return 'VETO'
    elif score <= 50:
        return 'FAIL'
    elif score <= 75:
        return 'FLAW'
    elif score <= 90:
        return 'WELL'
    else:
        return 'PASS'


def __calc_avg_score_with_weight(scores: list, weights: list) -> int or None:
    sum_score = 0
    sum_weight = 0
    for score, weight in zip(scores, weights):
        if score is None:
            continue
        elif weight == AnalysisResult.WEIGHT_ONE_VOTE_VETO:
            if score != AnalysisResult.SCORE_PASS:
                return 0
        else:
            sum_score += score * weight
            sum_weight += weight
    return (sum_score / sum_weight) if sum_weight > 0 else None


def generate_analysis_report(result: dict, file_path: str, analyzer_name_dict: dict = {}, stock_name_dict: dict = {}):
    wb = openpyxl.Workbook()
    ws_score = wb.active
    ws_score.title = 'Score'
    ws_comments = wb.create_sheet('Comments')

    ws_score['A1'] = 'Securities\\Analyzer'
    ws_comments['A1'] = 'Securities\\Analyzer'

    ROW_OFFSET = 2
    all_weight = []
    all_score = []

    column = 1
    for analyzer_uuid, analysis_result in result.items():
        # Note that this function will generate the report column by column
        #   The first column is the securities code and name
        #   The first row of each column is the name of analyzer
        # So we need to record the score for each cell, then we can calculate the total score by row at the end

        # Write securities column
        if column == 1:
            # The first run. Init the total score list here.
            # Flaw: The first column of result should be the full one. Otherwise the index may out of range.
            all_score = [[] for _ in range(0, len(analysis_result))]
            all_weight = [[] for _ in range(0, len(analysis_result))]

            row = 2
            col = index_to_excel_column_name(column)
            for r in analysis_result:
                securities_name = stock_name_dict.get(r.securities, '')
                display_text = (r.securities + ' | ' + securities_name) if securities_name != '' else r.securities
                ws_score[col + str(row)] = display_text
                ws_comments[col + str(row)] = display_text
                row += 1
            column = 2

        # Write analyzer name
        row = 1
        col = index_to_excel_column_name(column)
        analyzer_name = analyzer_name_dict.get(analyzer_uuid, analyzer_uuid)
        ws_score[col + str(row)] = analyzer_name
        ws_comments[col + str(row)] = analyzer_name

        # Write scores
        row = ROW_OFFSET
        for r in analysis_result:
            ws_score[col + str(row)] = r.score if r.score is not None else '-'
            ws_comments[col + str(row)] = r.reason

            if r.score is not None:
                all_score[row - ROW_OFFSET].append(r.score)
                all_weight[row - ROW_OFFSET].append(r.weight)
            fill_style = __score_to_fill_style(r.score)

            ws_score[col + str(row)].fill = fill_style
            ws_comments[col + str(row)].fill = fill_style
            row += 1
        column += 1

    # Write total score
    row = 1
    col_rate = index_to_excel_column_name(column)
    col_vote = index_to_excel_column_name(column + 1)

    for scores, weights in zip(all_score, all_weight):
        if row == 1:
            ws_score[col_vote + str(row)] = 'Vote'
            ws_comments[col_vote + str(row)] = 'Vote'
            ws_score[col_rate + str(row)] = 'Total Rate'
            ws_comments[col_rate + str(row)] = 'Total Rate'
            row = 2

        if len(scores) > 0:
            # min_score = min(score)
            avg_score = __calc_avg_score_with_weight(scores, weights)
        else:
            # min_score = None
            avg_score = None
        # fill_text = __score_to_fill_text(min_score)
        # fill_style = __score_to_fill_style(min_score)

        fill_text = __score_to_fill_text(avg_score)
        fill_style = __score_to_fill_style(avg_score)

        # ------------------- Rate -------------------

        if avg_score is not None:
            ws_score[col_rate + str(row)] = str(int(avg_score))
            ws_comments[col_rate + str(row)] = str(int(avg_score))
        else:
            ws_score[col_rate + str(row)] = '-'
            ws_comments[col_rate + str(row)] = '-'

        ws_score[col_rate + str(row)].fill = fill_style
        ws_comments[col_rate + str(row)].fill = fill_style

        # ------------------- Vote -------------------

        ws_score[col_vote + str(row)] = fill_text
        ws_comments[col_vote + str(row)] = fill_text

        ws_score[col_vote + str(row)].fill = fill_style
        ws_comments[col_vote + str(row)].fill = fill_style

        row += 1

    # Write file
    wb.save(file_path)











