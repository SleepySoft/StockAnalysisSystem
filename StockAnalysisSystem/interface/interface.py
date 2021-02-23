import datetime
import pandas as pd


class SasInterface:
    """
    This class declares the StockAnalysisSystem interface.
    The interface implementation MUST implements all this function for the compatibility.
    The function of this interface will be extended if necessary but we'd better not to change the existing declarations
    ALL the function parameters and return value should be * SERIALIZABLE *.
    """
    def __init__(self):
        pass

    def if_init(self, *args, **kwargs) -> bool:
        """
        Init interface. Different interface needs different parameters. This function is out of sas interface scope.
        :param args: The list args
        :param kwargs: The key-value args
        :return: True if success else False
        """
        pass

    # ----------------------------- Check & Prob ------------------------------

    def sas_service_prob(self) -> dict:
        pass

    def sas_service_check(self) -> dict:
        pass

    # --------------------------- System operation  ---------------------------

    def sas_get_service_config(self) -> dict:
        pass

    def sas_set_service_config(self, config: dict) -> bool:
        pass

    # ------------------------------- Resource --------------------------------

    def sas_get_resource(self, res_id: str, key: str or [str]) -> any or [any]:
        """
        Get resource from sas service. The resource can be any data that user can access and serializable.
        One resource id will have multiple key-value.
        The typical resource is ProgressRate. The client can polling the ProgressRate for updating the progress display.
        :param res_id: The id of resource.
        :param key: The key of the resource data that you want to retrieve.
        :return: The resource data. If the key is list, the data list should match the key order. None if data invalid.
        """
        pass

    def sas_find_resource(self, tags: str or [str]) -> [str]:
        """
        Find resource id by resource tags. The resource will be retrieved if any one of its tags in the list.
        :param tags: The tag or tags for finding the resource.
        :return: Resource ids. Empty list if no resource matches.
        """
        pass

    def sas_delete_resource(self, res_id: str or [str]) -> bool:
        """
        Delete resource by id from sas service.
        :param res_id: The id or id list of the resource that you want to delete.
        :return: True if success else False
        """
        pass

    # --------------------------------- Query ---------------------------------

    def sas_query(self, uri: str, identity: str or [str] = None, time_serial: tuple = None, **extra) -> pd.DataFrame or None:
        """
        Query data.
        :param uri: The uri of data. It's a MUST parameter and should be a valid str.
        :param identity: The securities id. None if no sub securities or get all its securities.
        :param time_serial: Tuple of time as (since, until).
        :param extra: Extra data for query. TBD.
        :return: The query result as pd.DataFrame
        """
        pass

    # -------------------------------- Datahub --------------------------------

    def sas_execute_update(self, uri: str, identity: str or [str] = None,
                           time_serial: tuple = None, force: bool = False, **extra) -> str:
        """
        Post a async update task.
        :param uri: The uri that you want to update. It's a MUST parameter and should be a valid str.
        :param identity: The securities id. If None, it will update all sub securities of this uri.
        :param time_serial: Update time range. None for auto detection (incremental update).
        :param force: True for full volume update else incremental update.
        :param extra: Extra data for update. TBD.
        :return: The update task resource id. You can get update progress by this id
        """
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

    def sas_get_trading_days(self, since: datetime.date, until: datetime.date) -> [datetime.date]:
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
