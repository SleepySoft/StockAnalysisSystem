import re

from .dependency import *
from .df_utility import *
from ..DataHubEntry import DataHubEntry
from ..Database.DatabaseEntry import DatabaseEntry


class FactorEngine:
    """
    The format of the formula:
        [A] = ([B] + [C]) / [D] ; [D] = [E] + [F] ; [F] = [G] * [H]
        The fields should be surrounded by []
        Multiple expression should be separated by ;
        The calculation should be supported by DataFrame
    """

    FIELD_FINDER = re.compile(r'(?<=\[).*?(?=\])')

    def __init__(self, formula: str, comments: str):
        self.__formula = formula
        self.__comments = comments

        # Need calculate
        self.__depends = []
        self.__provides = []
        self.__eval_formula = ''

        self.__parse_formula()

    def prob(self) -> ():
        return self.provides(), self.depends(), self.comments(), self.entry(), None, None, None

    def entry(self):
        return self.calculate

    def depends(self) -> list or str:
        return self.__depends

    def provides(self) -> list or str:
        return self.__provides

    def comments(self) -> str:
        return self.__comments

    def calculate(self, identity: str or [str], time_serial: tuple, mapping: dict,
                  data_hub: DataHubEntry, database: DatabaseEntry, extra: dict) -> pd.DataFrame or None:
        # Need implementation
        assert False

    def eval_formula(self) -> str:
        return self.__eval_formula

    def __parse_formula(self):
        self.__formula.replace('\r', '')
        self.__formula.replace('\n', ';')
        expressions = self.__formula.split(';')

        all_fields = []
        result_expressions = {}
        dependency = Dependency()

        # Split and analysis the sub expressions
        for exp in expressions:
            if exp.strip() == '':
                continue
            provides, depends = self.__parse_single_expression(exp)
            if len(provides) == 0 or len(depends) == 0:
                continue
            all_fields.extend(depends)
            all_fields.append(provides)
            result_expressions[provides] = exp
            dependency.add_dependence(provides, depends)

        # Sort the calculation chain
        eval_exp_order = []
        ordered_result = dependency.sort_by_dependency()
        result_expressions_copy = result_expressions.copy()
        for result in ordered_result:
            if result in result_expressions_copy.keys():
                eval_exp_order.append(result_expressions_copy.get(result))
                del result_expressions_copy[result]
        for key, val in result_expressions_copy.items():
            eval_exp_order.append(val)
        self.__eval_formula = '\n'.join(eval_exp_order)

        self.__eval_formula = self.__eval_formula.replace('[', "df['")
        self.__eval_formula = self.__eval_formula.replace(']', "']")

        # Not only the final result, but also the mid result
        self.__provides = list(result_expressions.keys())

        # Calculate the outer depends
        all_fields = list(set(all_fields))
        self.__depends = [field for field in all_fields if field not in self.__provides]

    @staticmethod
    def __parse_single_expression(exp: str) -> (str, [str]):
        parts = exp.split('=')
        if len(parts) != 2:
            print('Error: An Expression should has one "="')
            return '', []

        left = parts[0].strip()
        right = parts[1].strip()
        if len(left) == 0 or len(right) == 0:
            print('Error: An Expression should not be empty in both side of "="')
            return '', []

        left_fields = FactorEngine.FIELD_FINDER.findall(left)
        right_fields = FactorEngine.FIELD_FINDER.findall(right)
        if len(left_fields) != 1 or len(right_fields) == 0:
            print('Error: Left side of "=" should have only one field '
                  'and right side of "=" should have at least one field')
            return '', []

        return left_fields[0], right_fields


class FinanceFactorEngine(FactorEngine):
    def __init__(self, formula: str, comments: str):
        super(FinanceFactorEngine, self).__init__(formula, comments)

    def calculate(self, identity: str or [str], time_serial: tuple, mapping: dict,
                  data_hub: DataHubEntry, database: DatabaseEntry, extra: dict):
        df = query_finance_pattern(data_hub, identity, time_serial, self.depends(), mapping)
        eval_formula = self.eval_formula()
        exec(eval_formula)
        return df[self.provides() + ['stock_identity', 'period']]


# ----------------------------------------------------------------------------------------------------------------------

def dispatch_calculation_pattern(factor: str, identity: str or [str], time_serial: tuple, mapping: dict,
                                 data_hub: DataHubEntry, database: DatabaseEntry, extra: dict,
                                 FACTOR_TABLE) -> pd.DataFrame or None:
    for uuid, prob in FACTOR_TABLE.items():
        if prob is None or len(prob) != 7:
            continue
        provides, depends, comments, entry, _, _, _ = prob
        if factor in provides:
            return entry(identity, time_serial, mapping, data_hub, database, extra)
    return None


def query_finance_pattern(data_hub: DataHubEntry, identity: str,
                          time_serial: tuple, fields: list, mapping: dict) -> pd.DataFrame:
    query_fields = [mapping.get(f, f) for f in fields]
    query_fields = list(set(query_fields))

    if 'period' in query_fields:
        query_fields.remove('period')
    if 'stock_identity' in query_fields:
        query_fields.remove('stock_identity')

    data_utility = data_hub.get_data_utility()
    df = data_utility.auto_query(identity, time_serial, query_fields, join_on=['stock_identity', 'period'])

    df.fillna(0.0, inplace=True)
    df = df.sort_values('period', ascending=False)

    inv_dict = {v: k for k, v in mapping.items()}
    df = df.rename(inv_dict, axis='columns')

    return df


# ----------------------------------------------------- Test Entry -----------------------------------------------------

def test_factor_engine():
    fe = FactorEngine('[资本收益率] = [息税前利润] / ([净营运资本] + [固定资产]);'
                      '[息税前利润] = [税前利润] + [利息费用];'
                      '[净营运资本] = [应收账款] + [其他应收款] + [预付账款] + [存货] - [无息流动负债] + [长期股权投资] + [投资性房地产];'
                      '[无息流动负债] = [应付账款] + [预收款项] + [应付职工薪酬] + [应交税费] + [其他应付款] + [预提费用] + [递延收益] + [其他流动负债];',
                      '测试')


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_factor_engine()


# ----------------------------------------------------------------------------------------------------------------------

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


