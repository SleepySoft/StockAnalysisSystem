import datetime
import pandas as pd


class SasInterface:
    def __init__(self):
        pass

    def if_init(self, *args, **kwargs) -> bool:
        pass

    # ------------------------------- Resource --------------------------------

    def sas_get_resource(self, res_id: str, key: str or [str]) -> any or [any]:
        pass

    def sas_find_resource(self,  tags: str or [str]) -> [str]:
        pass

    def sas_delete_resource(self, res_id: str or [str]) -> bool:
        pass

    # --------------------------------- Query ---------------------------------

    def sas_query(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        pass

    # -------------------------------- Datahub --------------------------------

    def sas_execute_update(self, uri: str, identity: str or [str] = None, force: bool = False, **extra) -> str:
        pass

    def sas_get_all_uri(self) -> [str]:
        pass

    def sas_get_data_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        pass

    def sas_calc_update_range(self, uri: str, identity: str) -> (datetime.datetime, datetime.datetime):
        pass

    def sas_get_data_agent_probs(self) -> [dict]:
        """
        Get list of data agent prob
        :return: List of dict, dict key includes [uri, depot, identity_field, datetime_field]
        """
        pass

    def sas_get_data_agent_update_list(self, uri: str) -> [str]:
        pass

    # ----------------------------- Update Table -----------------------------

    def sas_get_local_data_range_from_update_table(self, update_tags: [str]) -> (datetime.datetime, datetime.datetime):
        pass

    def sas_get_last_update_time_from_update_table(self, update_tags: [str]) -> datetime.datetime:
        pass

    # -------------------------------- Analyzer --------------------------------

    def sas_execute_analysis(self, securities: str or [str], analyzers: [str], time_serial: (datetime, datetime),
                             enable_from_cache: bool = True, **kwargs) -> str:
        pass

    def sas_get_analyzer_probs(self) -> [str]:
        pass

    # ---------------------------------------------------- Utility -----------------------------------------------------

    def sas_auto_query(self, identity: str or [str], time_serial: tuple, fields: [str],
                       join_on: [str] = None) -> pd.DataFrame or [pd.DataFrame]:
        pass

    def sas_get_stock_info_list(self) -> [str]:
        pass

    def sas_get_stock_identities(self) -> [str]:
        pass

    def sas_guess_stock_identities(self, text: str) -> [str]:
        pass

    def sas_get_all_industries(self) -> [str]:
        pass

    def sas_get_industry_stocks(self, industry: str) -> [str]:
        pass

    def sas_stock_identity_to_name(self, stock_identities: str or [str]):
        pass

    def sas_get_support_index(self) -> dict:
        pass

    def sas_is_trading_day(self, _date: None or datetime.datetime or datetime.date, exchange: str):
        pass

# ------------------------------------------------------- Factor -------------------------------------------------------

    def sas_get_all_factors(self):
        pass

    def sas_get_factor_depends(self, factor: str) -> [str]:
        pass

    def sas_get_factor_comments(self, factor: str) -> str:
        pass

    def sas_factor_query(self, stock_identity: str, factor_name: str or [str],
                         time_serial: tuple, mapping: dict, **extra) -> pd.DataFrame or None:
        pass
