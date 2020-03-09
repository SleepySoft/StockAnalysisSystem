import traceback
from PyQt5.QtWidgets import QTableView
from Utiltity.ui_utility import *


# Seems slower
def display_df_with_model(df):
    model = DataFrameModel(df)
    table = QTableView()
    table.setModel(model)

    dlg = WrapperQDialog(table, False)
    dlg.exec()


# Seems faster
def display_df_with_function(df):
    table = QTableWidget()
    dlg = WrapperQDialog(table, False)
    write_df_to_qtable(df, table)
    dlg.exec()


def main():
    app = QApplication(sys.argv)

    df = pd.DataFrame.from_csv('./../TestData/Finance_BalanceSheet.csv')
    assert df is not None

    display_df_with_model(df)
    display_df_with_function(df)


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




