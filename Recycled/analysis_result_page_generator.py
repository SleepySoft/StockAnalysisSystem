import json
import traceback

from StockAnalysisSystem.core.config import Config
import StockAnalysisSystem.core.Utility.AnalyzerUtility as analyzer_util


def generate_result_page(result_path: str, name_dict_path: str, generate_sample: bool = False):
    try:
        print('Loading analyzer name table...')
        with open(name_dict_path, 'rt') as f:
            analyzer_name_dict = json.load(f)
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
            security_analyzer_table = analyzer_util.analysis_result_list_to_security_analyzer_table(analysis_result)

            print('Parsing analysis result...')
            for security, analyzer_result in security_analyzer_table:
                pass
            ANALYSIS_RESULT_DATAFRAME = {
                k.replace('.SZSE', '').replace('.SSE', ''):
                    analyzer_util.analyzer_table_to_dataframe(v).rename(columns=ANALYZER_NAME_DICT)
                for k, v in security_analyzer_table.items()}
            print('Converting to html...')
            ANALYSIS_RESULT_HTML = {k: v.to_html(index=True) for k, v in ANALYSIS_RESULT_DATAFRAME.items()}
            print('Load analysis result done.')
    except Exception as e:
        print('Load analysis result fail.')
        print(e)
        print(traceback.format_exc())
    finally:
        pass
