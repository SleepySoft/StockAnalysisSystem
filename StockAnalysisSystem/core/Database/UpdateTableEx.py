import traceback
from pymongo import MongoClient

from .NoSqlRw import *
from ..Utiltity.time_utility import *


class UpdateTableEx:
    def __init__(self, client: MongoClient, database: str = 'StockAnalysisSystem', table: str = 'UpdateTable'):
        self.__table = ItkvTable(client, database, table, 'tags', 'last_update')

    # ------------------------------------ Gets ------------------------------------

    def get_since(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['since'])
        return record[0].get('since') if record is not None and len(record) > 0 else None

    def get_until(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['until'])
        return record[0].get('until') if record is not None and len(record) > 0 else None

    def get_since_until(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['since', 'until'])
        return record[0].get('since') if record is not None and len(record) > 0 else None, \
               record[0].get('until') if record is not None and len(record) > 0 else None

    def get_last_update_time(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['last_update'])
        return record[0].get('last_update') if record is not None and len(record) > 0 else None

    def get_all_time(self, tags: [str]):
        record = self.__table.query(self.__normalize_tags(tags), keys=['since', 'until', 'last_update'])
        return record[0].get('since') if record is not None and len(record) > 0 else None, \
               record[0].get('until') if record is not None and len(record) > 0 else None, \
               record[0].get('last_update') if record is not None and len(record) > 0 else None

    def get_update_record(self, tags: [str]):
        return self.__table.query(self.__normalize_tags(tags))

    # ----------------------------------- Updates -----------------------------------

    def update_since(self, tags: [str], since: datetime or str) -> bool:
        if since is None:
            return False
        since = text_auto_time(since)
        old_since = self.get_since(tags)
        if old_since is None or since < old_since:
            # print('Update since: ' + str(tags) + ' -> ' + str(since))
            self.__table.upsert(self.__normalize_tags(tags), None, data={'since': since})
        return True

    def update_until(self, tags: [str], until: datetime or str) -> bool:
        if until is None:
            return False
        until = text_auto_time(until)
        old_until = self.get_until(tags)
        if old_until is None or until > old_until:
            # print('Update until: ' + str(tags) + ' -> ' + str(until))
            self.__table.upsert(self.__normalize_tags(tags), None, data={'until': until})
        return True

    def update_update_range(self, tags: [str], since: datetime or str, until: datetime or str) -> bool:
        ret1 = self.update_since(tags, since)
        ret2 = self.update_until(tags, until)
        return ret1 and ret2

    def update_latest_update_time(self, tags: [str]) -> bool:
        # print('Update latest update time: ' + str(tags) + ' -> ' + str(now()))
        self.__table.upsert(self.__normalize_tags(tags), None, data={'last_update': now()})
        return True

    def delete_update_record(self, tags: [str]) -> bool:
        self.__table.delete(self.__normalize_tags(tags))
        return True

    def clear_update_records(self) -> bool:
        self.__table.drop()
        return True

    # ------------------------------------------------------------------------------------------------------------------

    def __normalize_tags(self, tags: [str]) -> str:
        return ('.'.join(tags)).replace(' ', '') if isinstance(tags, (list, tuple)) else str(tags).strip()

    # TABLE = 'UpdateTableEx'
    # FIELD = ['serial', 'tags', 'since', 'until', 'latest_update']
    # INDEX_SINCE = 2
    # INDEX_UNTIL = 3
    # INDEX_LAST_UPDATE = 4
    #
    # def __init__(self, sql_db: SqlAccess):
    #     self.__sql_db = sql_db
    #
    # def get_since(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return None if len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_SINCE])
    #
    # def get_until(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return None if len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_UNTIL])
    #
    # def get_since_until(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return None if len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_SINCE]), \
    #            None if len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_UNTIL])
    #
    # def get_last_update_time(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return None if record is None or len(record) == 0 else text_auto_time(record[0][UpdateTableEx.INDEX_LAST_UPDATE])
    #
    # def get_all_time(self, tags: [str]):
    #     record = self.get_update_record(tags)
    #     return [None, None, None] if len(record) == 0 else \
    #         [text_auto_time(record[0][UpdateTableEx.INDEX_SINCE]),
    #          text_auto_time(record[0][UpdateTableEx.INDEX_UNTIL]),
    #          text_auto_time(record[0][UpdateTableEx.INDEX_LAST_UPDATE])]
    #
    # def update_since(self, tags: [str], since: datetime or str):
    #     return self.__update_date_field(tags, since, UpdateTableEx.INDEX_SINCE, lambda x, y: x < y)
    #
    # def update_until(self, tags: [str], until: datetime or str):
    #     return self.__update_date_field(tags, until, UpdateTableEx.INDEX_UNTIL, lambda x, y: x > y)
    #
    # def update_latest_update_time(self, tags: [str]):
    #     return self.__update_date_field(tags, today(), UpdateTableEx.INDEX_LAST_UPDATE, lambda x, y: x > y)
    #
    # def __update_date_field(self, tags: [str], date: datetime or str, field: int, compare):
    #     joined_tags = self.join_tags(tags)
    #     sql_update = ("UPDATE %s SET %s = '%s' WHERE tags = '%s';" %
    #                   (UpdateTableEx.TABLE, UpdateTableEx.FIELD[field], text_auto_time(date), joined_tags))
    #     sql_insert = ("INSERT INTO %s (tags, %s) VALUES ('%s', '%s');" %
    #                   (UpdateTableEx.TABLE, UpdateTableEx.FIELD[field], joined_tags, text_auto_time(date)))
    #
    #     record = self.get_update_record(tags)
    #     if record is None or len(record) == 0:
    #         return self.__sql_db.QuickExecuteDML(sql_insert, True)
    #     elif record[0][field] is None or compare(text_auto_time(date), text_auto_time(record[0][field])):
    #         return self.__sql_db.QuickExecuteDML(sql_update, True)
    #     else:
    #         return True
    #
    # def get_update_record(self, tags: [str]) -> []:
    #     joined_tags = self.join_tags(tags)
    #     return self.__sql_db.ListFromDB(
    #         UpdateTableEx.TABLE, UpdateTableEx.FIELD, "tags = '%s'" % joined_tags)
    #
    # def delete_update_record(self, tags: [str]):
    #     joined_tags = self.join_tags(tags)
    #     sql_delete = ("DELETE FROM %s WHERE tags = '%s';" % (UpdateTableEx.TABLE, joined_tags))
    #     return self.__sql_db.QuickExecuteDML(sql_delete, True)
    #
    # def join_tags(self, tags: [str]) -> str:
    #     return '.'.join(tags)







