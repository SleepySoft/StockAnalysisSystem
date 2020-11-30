import datetime
import pandas as pd
from .interface_util import *


class SasInterface:
    def __init__(self):
        pass

    # --------------------------------- Query ---------------------------------

    def sas_query(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        pass

    # -------------------------------- Datahub --------------------------------

    def sas_update(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> bool:
        pass

    def sas_get_data_agent_probs(self) -> [dict]:
        """
        Get list of data agent prob
        :return: List of dict, dict key includes [uri, depot, identity_field, datetime_field]
        """
        pass

    def sas_get_data_agent_update_list(self, uri: str) -> [str]:
        pass

    # -------------------------------- Analyzer --------------------------------

    def sas_start_analysis(self, securities: str or [str], analyzers: [str],
                           time_serial: (datetime, datetime),
                           enable_from_cache: bool = True) -> TaskFuture:
        pass

    def sas_get_analyzer_probs(self) -> [str]:
        pass

