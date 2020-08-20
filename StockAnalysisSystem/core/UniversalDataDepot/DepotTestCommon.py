import string
import pandas as pd
from .DepotInterface import DepotInterface


# ----------------------------------------------------------------------------------------------------------------------

def get_dataframe_cell(df: pd.DataFrame, column: str, index: int or dict) -> any:
    if column not in df.columns:
        return None
    if isinstance(index, int):
        return df[column].iloc[index] if index < len(df) else None
    elif isinstance(index, dict):
        sub_df = df
        for k, v in index.items():
            if k not in sub_df.columns:
                print('No column: ' + k)
                return None
            sub_df = sub_df[sub_df[k] == v]
        if sub_df.empty:
            return None
        elif len(sub_df) > 1:
            print('Multiple value.')
            return None
        else:
            return sub_df[column].iloc[0]
    else:
        return None


# ----------------------------------------------------------------------------------------------------------------------

def basic_rw_test(depot: DepotInterface):
    depot.drop()

    # ---------------------------------------------------------------------------------

    dataset1 = pd.DataFrame({
        'pk1': list(string.ascii_uppercase)[:10],           # A - J
        'pk2': range(10),                                   # 0 - 9
        'field1': ['Field1_' + c for c in list(string.ascii_uppercase)[:10]],   # Field1_A - Field1_J
        'field2': ['Field2_' + str(i) for i in range(10)],                      # Field2_0 - Field2_9
    })

    depot.upsert(dataset1)
    # Verify not have duplicate collections
    depot.upsert(dataset1)

    df = depot.query()
    assert get_dataframe_cell(df, 'pk1', 0) == 'A'
    assert get_dataframe_cell(df, 'pk2', 9) == 9
    assert get_dataframe_cell(df, 'field1', {'pk1': 'C'}) == 'Field1_C'
    assert get_dataframe_cell(df, 'field2', {'pk2': 7}) == 'Field2_7'

    # ---------------------------------------------------------------------------------

    dataset2 = pd.DataFrame({
        'pk1': list(string.ascii_uppercase)[5:15],      # F - O
        'pk2': range(100, 110),                         # 100 - 109
        'field2': ['Field2_' + str(i) for i in range(100, 110)],                    # Field2_100 - Field2_109
        'field3': ['field3_' + c for c in list(string.ascii_uppercase)[5:15]],      # Field3_F - Field3_O
    })
    depot.upsert(dataset2)

    df = depot.query()
    assert get_dataframe_cell(df, 'field2', {'pk1': 'F', 'pk2': 5}) == 'Field2_5'
    assert get_dataframe_cell(df, 'field2', {'pk1': 'J', 'pk2': 9}) == 'Field2_9'
    assert get_dataframe_cell(df, 'field2', {'pk1': 'F', 'pk2': 100}) == 'Field2_100'
    assert get_dataframe_cell(df, 'field2', {'pk1': 'J', 'pk2': 104}) == 'Field2_104'

    # ---------------------------------------------------------------------------------

    dataset3 = pd.DataFrame({
        'pk1': ['F', 'G', 'H', 'I', 'J', 'F', 'G', 'H', 'I', 'J'],
        'pk2': [5, 6, 7, 8, 9, 100, 101, 102, 103, 104],
        'field1': ['X' + str(i) for i in range(10)],
        'field2': ['Y' + str(i) for i in range(100, 110)],
        'field3': ['Z' + str(i) for i in range(1000, 1010)],
    })
    depot.upsert(dataset3)

    df = depot.query()
    assert get_dataframe_cell(df, 'field1', {'pk1': 'F', 'pk2': 5}) == 'X0'
    assert get_dataframe_cell(df, 'field2', {'pk1': 'F', 'pk2': 5}) == 'Y100'
    assert get_dataframe_cell(df, 'field3', {'pk1': 'F', 'pk2': 5}) == 'Z1000'

    assert get_dataframe_cell(df, 'field1', {'pk1': 'J', 'pk2': 104}) == 'X9'
    assert get_dataframe_cell(df, 'field2', {'pk1': 'J', 'pk2': 104}) == 'Y109'
    assert get_dataframe_cell(df, 'field3', {'pk1': 'J', 'pk2': 104}) == 'Z1009'


def basic_interface_test(depot: DepotInterface):
    length = depot.length()

    pk1_min, pk1_max = depot.range_of('pk1')
    pk2_min, pk2_max = depot.range_of('pk2')

    field1_min, field1_max = depot.range_of('field1')
    field2_min, field2_max = depot.range_of('field2')
    field3_min, field3_max = depot.range_of('field3')

    pk1_distinct = depot.distinct_value_of_field('pk1')
    all_fields = depot.all_fields()

    print(length)

    print(pk1_min, ' - ', pk1_max)
    print(pk2_min, ' - ', pk2_max)

    print(field1_min, ' - ', pk1_max)
    print(field2_min, ' - ', field2_max)
    print(field3_min, ' - ', field3_max)

    print(pk1_distinct)
    print(all_fields)
