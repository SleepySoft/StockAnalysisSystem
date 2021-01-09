import datetime
import pandas as pd


class SasInterface:
    def __init__(self):
        pass

    def if_init(self, *args, **kwargs) -> bool:
        pass

    # ------------------------------- Resource --------------------------------

    def sas_get_resource(self, res_id: str, res_name: str or [str]) -> any or [any]:
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

    # ------------------------------------------------------------------------------------------------------------------

    def sas_get_stock_info_list(self) -> [str]:
        pass

    def sas_get_stock_identities(self) -> [str]:
        pass

    def sas_guess_stock_identities(self, text: str) -> [str]:
        pass



