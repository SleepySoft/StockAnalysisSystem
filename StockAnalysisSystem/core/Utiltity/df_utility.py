import traceback
import numpy as np
import pandas as pd
import datetime as datetime
from os import sys, path


def get_series_item(series: pd.Series, order: int, default: any = None) -> any:
    slice_list = series.tolist()
    return slice_list[order] if order < len(slice_list) else default


def get_dataframe_slice_item(df_slice, field: str, order: int = 0, default: any = None) -> any:
    if len(df_slice) == 0 or field not in df_slice.columns:
        return default
    field_series = df_slice[field]
    return get_series_item(field_series, order, default)


def check_date_continuity(df: pd.DataFrame, field: str) -> tuple:
    """
    Check the continuity of a date format column in a DataFrame
    :param df: DataFrame for check
    :param field: The datetime filed you want to check
    :return: tuple (continuity: bool, start date: datetime, end date: datetime)
    """
    date_serial = pd.Series(data=1, index=df[field])
    date_serial.sort_index()
    min_date = min(date_serial.index)
    max_date = max(date_serial.index)
    date_serial.reindex(index=pd.date_range(min_date, max_date), fill_value=0)
    continuity = (0 not in date_serial.values)
    return continuity, min_date, max_date


def concat_dataframe_row_by_index(dfs: [pd.DataFrame]) -> pd.DataFrame:
    """
    Concat DataFrame by row. Remove the rows in the result which has duplicated index.
    :param dfs: The list of DataFrame you want to concat.
    :return: The result DataFrame
    """
    df = pd.concat(dfs)
    df = df.loc[~df.index.duplicated(keep='first')]
    return df


def concat_dataframe_by_row(dfs: [pd.DataFrame], unique_column: str = None) -> pd.DataFrame:
    df = pd.concat(dfs, axis=0, ignore_index=True)
    df.reindex()

    # Delete duplicate column
    # _, i = np.unique(df.columns, return_index=True)
    # df = df.iloc[:, i]

    # Delete row with duplicate value in specified column
    picked_lines = []
    if unique_column is not None and len(unique_column) > 0 and unique_column in df.columns:
        grouped = df.groupby(unique_column)
        for _, g in df.groupby(unique_column):
            picked_line = None
            for row_index, row in g.iterrows():
                if picked_line is None:
                    picked_line = row
                else:
                    for i in range(0, len(row)):
                        if pd.isna(picked_line[i]):
                            picked_line[i] = row[i]
            if picked_line is not None:
                picked_lines.append(picked_line)
        df = pd.concat(picked_lines)

        # df = pd.concat(g for _, g in df.groupby(unique_column) if len(g) > 1)
    return df


def clip_dataframe(df: pd.DataFrame, indexes: [int], columns: [str]):
    """
    Clip DataFrame by specified indexes and columns. If data not exists, nan will be filled.
    :param df: The DataFrame you want to clip
    :param indexes: The indexes you pick
    :param columns: The columns you pick
    :return: The result DataFrame
    """
    df_sub = pd.DataFrame()
    for c in columns:
        if c not in df.columns:
            serial = np.empty(df.shape[0])
            serial.fill(np.nan)
        else:
            serial = df[c]
        df_sub.insert(len(df_sub.columns), c, serial)
    return df_sub.loc[indexes]


def slice_dataframe_by_datetime(df: pd.DataFrame, since: datetime = None,
                                until: datetime = None, column: str = None) -> pd.DataFrame or None:
    if column is not None:
        if column == '' or column not in df.columns:
            return None
        if since is not None:
            df = df[df[column] >= since]
        if until is not None:
            df = df[df[column] <= until]
        return df
    else:
        if since is not None:
            df = df[df.index >= since]
        if until is not None:
            df = df[df.index <= until]
        return df


def merge_on_columns(df1: pd.DataFrame, df2: pd.DataFrame, columns: str or [str]):
    if df1 is None:
        return df2
    if df2 is None:
        return df1
    if not isinstance(columns, (list, tuple)):
        columns = [columns]
    # https://stackoverflow.com/questions/19125091/pandas-merge-how-to-avoid-duplicating-columns/19125531#19125531
    diff_cols = list(df2.columns.difference(df1.columns))
    # if len(diff_cols) == 0:
    #     df = pd.merge(df1, df2, how='left', on=columns, sort=False)
    # else:
    merge_columns = diff_cols + columns
    df = pd.merge(df1, df2[merge_columns], how='inner', on=columns, sort=False)
    return df


def group_as_list(df: pd.DataFrame, group_by: str or list) -> pd.DataFrame:
    if not isinstance(group_by, (list, tuple)):
        group_by = [group_by]
    return df.groupby(group_by, as_index=False).agg(lambda x: list(x))


def group_as_dict(df: pd.DataFrame, group_by: str or list) -> pd.DataFrame:
    if not isinstance(group_by, (list, tuple)):
        group_by = [group_by]
    return df.groupby(group_by, as_index=False).agg(lambda x: {k: v for d in x.dropna() for k, v in d.items()})


# ----------------------------------------------------------------


def MergeDataFrameOnIndex(df_l: pd.DataFrame, df_r: pd.DataFrame):
    if df_l is None:
        return df_r
    if df_r is None:
        return df_l
    return pd.merge(df_l, df_r, left_index=True, right_index=True, how='outer')


def MergeDataFrameOnColumn(df_l: pd.DataFrame, df_r: pd.DataFrame, on_col: str):
    if df_l is None or on_col not in df_l.columns:
        return df_r
    if df_r is None or on_col not in df_r.columns:
        return df_l
    return pd.merge(df_l, df_r, on=on_col, how='outer')


# return (copied, uncopied)
def DataFrameColumnCopy(df_from: pd.DataFrame, df_to: pd.DataFrame, columns: [str]) -> (int, int):
    copied = uncopied = 0
    for c in columns:
        if c not in df_from.columns.tolist():
            uncopied += 1
            continue
        col = df_from[c]
        if c not in df_to.columns.tolist():
            df_to.insert(len(df_to.columns), c, col.copy())
        else:
            df_to[c] = col.copy()
        copied += 1
    return copied, uncopied


# ----------------------------------------------------- Test Code ------------------------------------------------------

def generate_test_dataframe(rows: [str], cols: [str]) -> pd.DataFrame:
    """
    Generate a test DataFrame
    :param rows: The rows you want to generate.
    :param cols: The columns you want to generate
    :return: The generated DataFrame, which's items are contracted by row and column.

    :example: generate_test_dataframe(range(1, 5), ['a', 'b', 'c', 'd'])
        a   b   c   d
    0  1A  1B  1C  1D
    1  2A  2B  2C  2D
    2  3A  3B  3C  3D
    3  4A  4B  4C  4D
    """
    df = pd.DataFrame()
    for col in cols:
        df[col] = pd.Series([str(row).upper() + str(col).upper() for row in rows])
    return df


def test_concat_dataframe_by_index():
    df1 = pd.DataFrame(data={
        'a': ['1A', '2A', '3A'],
        'b': ['1B', '2B', '3B'],
        'c': ['1C', '2C', '3C'],
    }, index=['2001-01-01', '2001-01-02', '2001-01-03'])
    df2 = pd.DataFrame(data={
        'a': ['3Ax', '4A', '5A'],
        'b': ['3Bx', '4B', '5B'],
        'c': ['3Cx', '4C', '5C'],
    }, index=['2001-01-03', '2001-01-04', '2001-01-05'])
    print(df1)
    print('---------------------------------------------------------------')
    print(df2)
    print('---------------------------------------------------------------')

    df = concat_dataframe_row_by_index([df1, df2])
    print(df)


def test_clip_dataframe():
    df = pd.DataFrame(data={
        'a': ['1A', '2A', '3A', '4A'],
        'b': ['1B', '2B', '3B', '4A'],
        'c': ['1C', '2C', '3C', '4A'],
        'd': ['1D', '2D', '3D', '4D'],
        'e': ['1E', '2D', '3E', '4E'],
    })
    df.reindex()
    df = clip_dataframe(df, [1, 3], ['a', 'c', 'e'])
    print(df)


def test_slice_dataframe_by_datetime():
    df1 = pd.DataFrame(data={
        'a': ['1A', '2A', '3A', '4A'],
        'b': ['1B', '2B', '3B', '4A'],
        'c': ['1C', '2C', '3C', '4A'],
        'd': ['1D', '2D', '3D', '4D'],
        'e': ['1E', '2D', '3E', '4E'],
    }, index=['2001-01-01', '2001-01-03', '2001-02-04', '2001-05-05'])

    df = slice_dataframe_by_datetime(df1, '2001-01-02', '2001-02-04')
    print(df)
    print('---------------------------------------------------------------')

    df = slice_dataframe_by_datetime(df1, '2001-01-02', None)
    print(df)
    print('---------------------------------------------------------------')

    df = slice_dataframe_by_datetime(df1, None, '2001-02-04')
    print(df)
    print('---------------------------------------------------------------')

    df2 = pd.DataFrame(data={
        'a': ['1A', '2A', '3A', '4A'],
        'b': ['1B', '2B', '3B', '4A'],
        'c': ['1C', '2C', '3C', '4A'],
        'date': ['2001-01-01', '2001-01-03', '2001-02-04', '2001-05-05'],
        'e': ['1E', '2D', '3E', '4E'],
    })

    df = slice_dataframe_by_datetime(df2, '2001-01-02', '2001-02-04', 'date')
    print(df)
    print('---------------------------------------------------------------')

    df = slice_dataframe_by_datetime(df2, '2001-01-02', None, 'date')
    print(df)
    print('---------------------------------------------------------------')

    df = slice_dataframe_by_datetime(df2, None, '2001-02-04', 'date')
    print(df)
    print('---------------------------------------------------------------')


def test_concat_dataframe_by_row():
    df1 = generate_test_dataframe(range(1, 5), ['a', 'b', 'c', 'd'])
    df2 = generate_test_dataframe(range(3, 6), ['d', 'e', 'f', 'g'])
    df = concat_dataframe_by_row([df1, df2])
    print('-----------------------------------------------------------')
    print(df1)
    print('-----------------------------------------------------------')
    print(df2)
    print('-----------------------------------------------------------')
    print('concat_dataframe_by_row([df1, df2])')
    print('-----------------------------------------------------------')
    print(df)


def test_concat_dataframe_by_row_with_duplicate_column():
    df1 = generate_test_dataframe(range(1, 5), ['a', 'b', 'c', 'd'])
    df2 = generate_test_dataframe(range(3, 6), ['c', 'd', 'e', 'f'])
    df2.columns = ['x', 'd', 'e', 'f']

    print('-----------------------------------------------------------')
    print(df1)
    print('-----------------------------------------------------------')
    print(df2)
    print('-----------------------------------------------------------')

    df = concat_dataframe_by_row([df1, df2], 'd')
    print('concat_dataframe_by_row([df1, df2])', 'd')
    print('-----------------------------------------------------------')
    print(df)


def test_entry():
    test_concat_dataframe_by_index()
    test_clip_dataframe()
    test_slice_dataframe_by_datetime()
    test_concat_dataframe_by_row()
    test_concat_dataframe_by_row_with_duplicate_column()


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











