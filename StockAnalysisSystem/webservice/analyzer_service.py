import json
import traceback
import pandas as pd

from StockAnalysisSystem.core.config import Config
import StockAnalysisSystem.core.Utiltity.AnalyzerUtility as analyzer_util


ANALYZER_NAME_DICT = {}
ANALYSIS_RESULT_HTML = {}
ANALYSIS_RESULT_TABLE = {}


def init(config: Config):
    return

    global ANALYZER_NAME_DICT
    global ANALYSIS_RESULT_HTML
    global ANALYSIS_RESULT_TABLE

    result_path = config.get('analysis_result_path', 'analysis_result.json')
    name_dict_path = config.get('analysis_name_dict_path', 'analyzer_names.json')

    try:
        print('Loading analyzer name table...')
        with open(name_dict_path, 'rt') as f:
            ANALYZER_NAME_DICT = json.load(f)
        print('Load analyzer name table done.')
    except Exception as e:
        print('Load analyzer name table fail.')
        print(e)
        print(traceback.format_exc())
    finally:
        pass

    try:
        with open(result_path, 'rt') as f:
            print('Loading analysis result...')
            analysis_result = analyzer_util.analysis_results_from_json(f)
            print('Convert analysis result...')
            analysis_result_table = analyzer_util.analysis_result_list_to_security_analyzer_table(analysis_result)
            ANALYSIS_RESULT_TABLE = {k.split('.')[0]: v for k, v in analysis_result_table.items()}
            print('Load analysis result done.')
    except Exception as e:
        print('Load analysis result fail.')
        print(e)
        print(traceback.format_exc())
    finally:
        pass


def data_frame_to_html_simple(df: pd.DataFrame) -> str:
    html = df.to_html(index=True)
    html = html.replace('\\n', '<br>')
    return html


data_frame_to_html = data_frame_to_html_simple


def analysis(security: str) -> str:
    global ANALYZER_NAME_DICT
    global ANALYSIS_RESULT_HTML

    security = security.split('.')[0]

    result = ANALYSIS_RESULT_HTML.get(security, None)
    if result is not None:
        return result

    if security not in ANALYSIS_RESULT_TABLE:
        return ''

    security_analysis_result = ANALYSIS_RESULT_TABLE[security]
    security_analysis_result_df = analyzer_util.analyzer_table_to_dataframe(security_analysis_result)
    security_analysis_result_df = security_analysis_result_df.rename(columns=ANALYZER_NAME_DICT)
    security_analysis_result_df = security_analysis_result_df.fillna('-')

    security_analysis_result_html = data_frame_to_html(security_analysis_result_df)
    ANALYSIS_RESULT_HTML[security] = security_analysis_result_html

    return security_analysis_result_html




