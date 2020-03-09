#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2019/02/02
@file: DataTable.py
@function:
@modify:
"""
from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

from Utiltity.common import *
from Database.SqlRw import SqlAccess


class AliasTable:
    """
    Table field : alias name | standard name | comments

    An alias name can only map to one standard name.
    An alias name can NOT also be a standard name.
    A standard name can be mapped to multiple alias name.

    When we meet a new name. It's standard name is empty. It's in ISOLATED mode.
    When we assign a standard name to an ISOLATED alias name. We need to update all the field that includes this name.
    When we rename a standard name. We need to update all the field that includes this name.
    """

    class Participant:
        def name(self) -> str: pass

        def get_using_names(self) -> [str]: pass

        def on_std_name_updating(self, old_name: str, new_name: str) -> (bool, str):
            """
            This function will be invoked before name updating.
            :param old_name: The old name
            :param new_name: The new name
            :return: (True if it's OK ; False if it's NOK,
                      The reason that why this name can not be changed)
            """
            nop(self)
            nop(old_name)
            nop(new_name)
            return True, ''

        def on_std_name_removed(self, name: str): pass

        def on_std_name_updated(self, old_name: str, new_name: str): pass

    TABLE = 'AliasTable'
    FIELD = ['alias_name', 'standard_name', 'comments']

    def __init__(self, sql_db: SqlAccess):
        self.__sql_db = sql_db
        self.__has_update = False
        self.__participants = []
        self.__using_name_list = []
        self.__alias_standard_table = {}    # Key: alias_name; Value: standard_name
        self.__standard_alias_table = {}    # Key: standard_name; Value: [alias_name]

    def init(self, auto: bool) -> bool:
        if auto:
            if not self.load_from_db():
                print('Error: Load Aliases Table Fail!')
                return False
        return True

    def register_participant(self, participant: Participant):
        self.__participants.append(participant)

    # ------------------------------------------------------------------------------------------------------------------

    def reset(self):
        self.__has_update = False
        self.__using_name_list = []
        self.__alias_standard_table = {}
        self.__standard_alias_table = {}

    def reload(self):
        self.load_from_db()

    def collect_names(self):
        names = []
        for participant in self.__participants:
            name = participant.get_using_names()
            names.extend(name)
        self.__using_name_list = list(set(names))

    def check_naming_error(self):
        pass

    # ------------------------------------------------------------------------------------------------------------------

    def add_alias(self, alias_name: str, standard_name: str) -> bool:
        # """
        # Add or re-assign a alias name to a standard name.
        #   > alias_name is empty: Illegal parameter, return False
        #   > alias_name is also a standard name: Illegal case, return False
        #   > standard_name is empty: Reset the alias-standard linkage
        #   > alias_name exists but haven't linked to a standard name: New assignment, check update all related fields.
        # :param alias_name: Must not be an empty string.
        # :param standard_name: Empty string to reset the alias-standard linkage.
        # :param reason: The reason that add this mapping.
        # :return: True if updated else False
        # """
        if alias_name == '' or alias_name == standard_name:
            return False
        if alias_name in self.__standard_alias_table.keys():
            return False
        self.__alias_standard_table[alias_name] = standard_name
        if standard_name not in self.__standard_alias_table.keys():
            self.__standard_alias_table[standard_name] = []
        if alias_name not in self.__standard_alias_table[standard_name]:
            self.__standard_alias_table[standard_name].append(alias_name)
        self.__has_update = True
        return True

        # exists_std_name = self.__alias_standard_table[alias_name]
        # if exists_std_name == standard_name:
        #     return True
        # if exists_std_name == '':
        #     updated = self.__handle_name_change(alias_name, standard_name, alias_name)
        # else:
        #     self.__alias_standard_table[alias_name] = standard_name
        #     updated = True
        # if updated:
        #     self.__has_update = True
        # return updated

    def del_alias(self, alias_name: str) -> bool:
        if alias_name == '':
            return False
        if alias_name in self.__alias_standard_table.keys():
            del self.__alias_standard_table[alias_name]
            self.__has_update = True
        for key in list(self.__standard_alias_table.keys()):
            val = self.__standard_alias_table[key]
            if alias_name in val:
                val.remove(alias_name)
                self.__has_update = True
            if len(val) == 0:
                del self.__standard_alias_table[key]
        return True

    def update_standard_name(self, standard_name: str, standard_name_new: str) -> (bool, str):
        update, reason = self.__query_name_updating(standard_name, standard_name_new)
        if not update:
            return update, reason

        for alias in self.__alias_standard_table.keys():
            if self.__alias_standard_table[alias] == standard_name:
                self.__alias_standard_table[alias] = standard_name_new
                self.__has_update = True

        if standard_name_new not in self.__standard_alias_table.keys():
            self.__standard_alias_table[standard_name_new] = {}
        if standard_name in self.__standard_alias_table.keys():
            # Merge alias and remove duplicates, finally del old standard name
            alias = self.__standard_alias_table[standard_name]
            alias.extend(self.__standard_alias_table[standard_name_new])
            self.__standard_alias_table[standard_name_new] = list(set(alias))
            del self.__standard_alias_table[standard_name]

        self.__notify_name_updated(standard_name, standard_name_new)

        return True, ''

    def del_standard_name(self, standard_name: str):
        if standard_name in self.__standard_alias_table:
            del self.__standard_alias_table[standard_name]
            self.__has_update = True
        for alias in self.__alias_standard_table.keys():
            if self.__alias_standard_table[alias] == standard_name:
                self.__alias_standard_table[alias] = ''
                self.__has_update = True
        if standard_name in self.__using_name_list:
            self.__using_name_list.remove(standard_name)
        self.__notify_name_removed(standard_name)

    # ------------------------------------------------------------------------------------------------------------------

    def standardize(self, name: list or str) -> list or str:
        if isinstance(name, str):
            return self.__do_standardize(name)
        elif isinstance(name, list):
            return [self.__do_standardize(n) for n in name]
        return None

    def get_standard_name(self, name: str) -> str:
        if name in self.__standard_alias_table.keys():
            return name
        return self.__alias_standard_table.get(name, '')

    def get_alias_standard_table(self) -> dict:
        return self.__alias_standard_table

    def get_standard_name_list(self) -> list:
        all_names = []
        all_names.extend(self.__using_name_list)
        all_names.extend(list(self.__standard_alias_table.keys()))
        return list(set(all_names))

    def get_uncategorized_name_list(self) -> list:
        tmp_list = []
        for key in self.__alias_standard_table.keys():
            if self.__alias_standard_table[key] == '':
                tmp_list.append(key)
        return tmp_list

    # --------------------------------------------------- Load/Save ---------------------------------------------------

    def check_save(self):
        if self.__has_update:
            self.__has_update = not self.dump_to_db()

    def load_from_db(self) -> bool:
        self.reset()
        tmp_list = self.__sql_db.ListFromDB(
            AliasTable.TABLE, AliasTable.FIELD)
        if tmp_list is None or len(tmp_list) == 0:
            return False
        for alias, standard, comments in tmp_list:
            self.add_alias(alias, standard)
        self.__has_update = False
        return True

    def dump_to_db(self) -> bool:
        tmp_list = []
        for alias in self.__alias_standard_table.keys():
            standard = self.__alias_standard_table[alias]
            tmp_list.append(alias)
            tmp_list.append(standard)
            tmp_list.append('')
        self.__sql_db.ListToDB(
            AliasTable.TABLE, tmp_list, -1, 3,
            AliasTable.FIELD)
        return True

    def load_from_csv(self, file_name: str):
        """
        Load alias - standard name mapping from a csv
        The CSV file should have columns named: 'alias' and 'standard'
        :param file_name: The CSV file that you want to load
        :return: True if OK. Else False
        """
        df = pd.read_csv(file_name, header=0)
        column_alias_name = df['alias']
        column_standard_name = df['standard']
        for alias, standard in zip(column_alias_name, column_standard_name):
            # self.add_alias(self.__trim_name(alias), standard)
            try:
                self.add_alias(alias.strip(), standard.strip())
            except Exception as e:
                self.add_alias(str(alias).strip(), str(standard).strip())
            finally:
                pass
        return True

    def dump_to_csv(self, file_name: str) -> str:
        tmp_list = []
        for k in self.__alias_standard_table.keys():
            tmp_list.append(k)
            alias = self.__alias_standard_table.get(k, [])
            tmp_list.append('|'.join(alias))
        for n in self.__uncategorized_name_list:
            tmp_list.append('-')
            tmp_list.append(n)
        df = pd.DataFrame(np.array(tmp_list).reshape(-1, 2))
        df.columns = ['standard_name', 'alias_name']
        try:
            df.to_csv(file_name, encoding='utf_8_sig')
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            pass

    # ---------------------------------------------------- private -----------------------------------------------------

    def __query_name_updating(self, old_std_name: str, standard_name: str):
        for participant in self.__participants:
            update, reason = participant.on_std_name_updating(old_std_name, standard_name)
            if not update:
                return False, reason
        return True, ''

    def __notify_name_updated(self, old_std_name: str, standard_name: str):
        for participant in self.__participants:
            participant.on_std_name_updated(old_std_name, standard_name)

    def __notify_name_removed(self, standard_name: str):
        for participant in self.__participants:
            participant.on_std_name_removed(standard_name)

    # def __handle_name_change(self, alias_name: str, standard_name, old_std_name: str) -> (bool, str):
    #     for listener in self.__listeners:
    #         update, reason = listener.on_std_name_updating(old_std_name, standard_name)
    #         if not update:
    #             return False, reason
    #
    #     self.__alias_standard_table[alias_name] = standard_name
    #     if standard_name not in self.__standard_alias_table.keys():
    #         self.__standard_alias_table.keys().append(standard_name)
    #
    #     for listener in self.__listeners:
    #         listener.on_std_name_updated(old_std_name, standard_name)
    #     return True, ''

    def __do_standardize(self, name: str):
        alias_name = name.strip()
        standard_name = self.get_standard_name(alias_name)
        return standard_name

    def __trim_name(self, name: str) -> str:
        name = name.strip()
        name = self.__trim_space(name)
        name = self.__trim_unit(name)
        return name

    def __trim_space(self, name) -> str:
        TRIM_LIST = [' ']
        return self.__list_trim(name, TRIM_LIST)

    def __trim_unit(self, name: str) -> str:
        # How to make it better? Regex? Semantic Analysis?
        TRIM_LIST = ['(万元)', '（万元）']
        return self.__list_trim(name, TRIM_LIST)

    @staticmethod
    def __list_trim(name: str, trim_list: [str]) -> str:
        for t in trim_list:
            name = name.replace(t, '')
        return name

    # ----------------------------------------- Cache for Quick Indexing -----------------------------------------

    def __find_alias(self, alias_name: str) -> str:
        pass

    # --------------------------------------------------- Build ---------------------------------------------------

    # def RebuildTable(self):
    #     self.__alias_standard_table.clear()
    #     self.__alias_standard_table.clear()
    #     self.__update_from_internet()
    #     # self.__update_from_local()
    #     return self.SaveTable()

    # def __update_from_internet(self) -> bool:
    #     df = self.__fetch_standard_table()
    #     if '英文表达法' not in df.columns and '会计科目名称' not in df.columns:
    #         print('Cannot find the column in web.')
    #         return False
    #     column_alias_name = df['英文表达法']
    #     column_standard_name = df['会计科目名称']
    #     for s, a in zip(column_standard_name, column_alias_name):
    #         self.__add_alias(self.__trim_name(s), a)
    #     return True
    #
    # def __update_from_local(self) -> bool:
    #     df = pd.read_csv('Utiltity/NameTable.csv', header=0)
    #     column_alias_name = df['英文']
    #     column_standard_name = df['中文']
    #     for s, a in zip(column_standard_name, column_alias_name):
    #         self.__add_alias(self.__trim_name(s), a)
    #     return True

    # @staticmethod
    # def __fetch_standard_table() -> pd.DataFrame:
    #     # From baike.baidu.com
    #     soup = Utiltity.common.GetWebAsSoap(
    #         'https://baike.baidu.com/item/%E4%BC%9A%E8%AE%A1%E7%A7%91%E7%9B%AE%E4%B8%AD%E8%8B%B1%E6%96%87%E5%AF%B9%E7%85%A7%20%EF%BC%88%E5%8C%97%E4%BA%AC%E5%B8%82%E5%AE%A1%E8%AE%A1%E5%B1%80%E5%8F%91%E5%B8%83%EF%BC%89',
    #         'utf-8')
    #     table = soup.find('table', {'log-set-param': 'table_view'})
    #     if table is None:
    #         return None
    #
    #     tr_list = table.findAll('tr')
    #     if len(tr_list) == 0:
    #         return None
    #
    #     df_list = []
    #     for tr in tr_list:
    #         tmp_list = []
    #         td_list = tr.findAll('td')
    #         if len(td_list) != 5:
    #             continue
    #         for td in td_list:
    #             div = td.find('div')
    #             if div is not None:
    #                 tmp_list.append(div.string.strip())
    #             else:
    #                 tmp_list.append('')
    #         df_list.extend(tmp_list)
    #
    #     df = pd.DataFrame(np.array(df_list).reshape(-1, 5))
    #     df.columns = df.iloc[0]
    #     df = df[1:]
    #
    #     # print(df)
    #     return df


# ----------------------------------------------------- Test Code ------------------------------------------------------

class TestAliasParticipant(AliasTable.Participant):
    def __init__(self):
        self.old_std_name = ''
        self.new_std_name = ''
        self.del_std_name = ''
        self.invoke_count = {
            'on_std_name_updating': 0,
            'on_std_name_removed': 0,
            'on_std_name_updated': 0,
        }
        self.reject = False
        self.reject_reason = ''

    def name(self) -> str:
        nop(self)
        return 'test_participant'

    def get_using_names(self) -> [str]:
        nop(self)
        return []

    def on_std_name_updating(self, old_name: str, new_name: str) -> (bool, str):
        self.old_std_name = old_name
        self.new_std_name = new_name
        self.invoke_count['on_std_name_updating'] += 1
        return not self.reject, self.reject_reason

    def on_std_name_removed(self, name: str):
        self.del_std_name = name
        self.invoke_count['on_std_name_removed'] += 1

    def on_std_name_updated(self, old_name: str, new_name: str):
        self.old_std_name = old_name
        self.new_std_name = new_name
        self.invoke_count['on_std_name_updated'] += 1


def __default_prepare_test() -> (AliasTable, TestAliasParticipant):
    data_path = root_path + '/Data/'
    sql_db = SqlAccess(data_path + 'sAsUtility.db')
    alias_table = AliasTable(sql_db)
    participant = TestAliasParticipant()
    alias_table.register_participant(participant)
    return alias_table, participant


def __default_prepare_test_data(alias_table: AliasTable):
    pass


def test_alias_multiple_mapping():
    alias_table, participant = __default_prepare_test()

    alias_table.add_alias('A1', 'S1')
    assert(alias_table.standardize('A1') == 'S1')
    alias_table.add_alias('A1', 'S2')
    assert(alias_table.standardize('A1') == 'S2')
    alias_table.add_alias('A1', 'S3')
    assert(alias_table.standardize('A1') == 'S3')

    alias_table.add_alias('A2', 'S3')
    alias_table.add_alias('A3', 'S3')
    assert(alias_table.standardize('A1') == 'S3')
    assert(alias_table.standardize('A2') == 'S3')
    assert(alias_table.standardize('A3') == 'S3')


def test_add_remove_alias():
    alias_table, participant = __default_prepare_test()

    alias_table.add_alias('A1', 'S1')
    alias_table.add_alias('A2', 'S1')
    alias_table.add_alias('A3', 'S3')

    alias_table.del_alias('A2')
    assert(alias_table.standardize('A1') == 'S1')
    assert(alias_table.standardize('A2') == '')
    assert(alias_table.standardize('A3') == 'S3')


def test_operation_denied():
    alias_table, participant = __default_prepare_test()

    alias_table.add_alias('A1', 'S1')
    assert(alias_table.add_alias('S1', 'S2') is False)
    assert(alias_table.add_alias('A2', 'A2') is False)


def test_update_standard_name_allowed():
    alias_table, participant = __default_prepare_test()

    alias_table.add_alias('A1', 'S1')
    alias_table.add_alias('A2', 'S1')
    alias_table.add_alias('A3', 'S2')

    alias_table.update_standard_name('S1', 'S2')
    assert(participant.invoke_count['on_std_name_updating'] == 1)
    assert(participant.invoke_count['on_std_name_updated'] == 1)
    assert(alias_table.standardize('A1') == 'S2')
    assert(alias_table.standardize('A2') == 'S2')
    assert(alias_table.standardize('A3') == 'S2')


def test_del_standard_name():
    alias_table, participant = __default_prepare_test()

    alias_table.add_alias('A1', 'S1')
    alias_table.add_alias('A2', 'S2')
    alias_table.add_alias('A3', 'S3')

    alias_table.del_standard_name('S1')
    assert(participant.invoke_count['on_std_name_removed'] == 1)
    assert(participant.del_std_name == 'S1')
    assert(alias_table.standardize('A1') == '')


def test_entry():
    test_alias_multiple_mapping()
    test_add_remove_alias()
    test_operation_denied()
    test_update_standard_name_allowed()
    test_del_standard_name()
    pass


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_entry()

    # If program reaches here, all test passed.
    print('All test passed.')


# ------------------------------------------------- Exception Handling -------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass













