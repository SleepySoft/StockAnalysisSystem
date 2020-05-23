import sys
import traceback
from functools import partial
from collections import OrderedDict

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QStyledItemDelegate, QTreeWidgetItem, QComboBox, QInputDialog, QFileDialog

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidget, QHBoxLayout, QTableWidgetItem, \
    QWidget, QPushButton, QDockWidget, QLineEdit, QAction, qApp, QMessageBox, QDialog, QVBoxLayout, QLabel, QTextEdit, \
    QListWidget, QShortcut

from .core import *
from .Utility.ui_utility import *


# ---------------------------------------------------- FilterEditor ----------------------------------------------------

class HistoricalFilter(LabelTag):
    def __init__(self):
        super(HistoricalFilter, self).__init__()

    # ---------------------------- Sets ----------------------------

    def set_sources(self, sources: [str]):
        self.__set_label_tags_str('sources', sources)

    def set_focus_label(self, label: str):
        self.__set_label_tags_str('focus_label', [label])

    def set_include_tags_str(self, ltags_str: [str]):
        if not HistoricalFilter.__check_tags_str(ltags_str):
            return False
        self.__set_label_tags_str('include_tags', ltags_str)
        return True

    def set_exclude_tags_str(self, ltags_str: [str]):
        if not HistoricalFilter.__check_tags_str(ltags_str):
            return False
        self.__set_label_tags_str('exclude_tags', ltags_str)
        return True

    def add_include_tags_str(self, ltags_str: [str]):
        if not HistoricalFilter.__check_tags_str(ltags_str):
            return False
        self.__add_label_tags_str('include_tags', ltags_str)
        return True

    def add_exclude_tags_str(self, ltags_str: [str]):
        if not HistoricalFilter.__check_tags_str(ltags_str):
            return False
        self.__add_label_tags_str('exclude_tags', ltags_str)
        return True

    # ---------------------------- Gets ----------------------------

    def get_sources(self) -> [str]:
        return self.get_tags('sources')

    def get_focus_label(self) -> str:
        focus_label = self.get_tags('focus_label')
        if focus_label is None or len(focus_label) == 0:
            return ''
        if isinstance(focus_label, (list, tuple)):
            return focus_label[0]
        return focus_label

    def get_include_tags(self) -> {}:
        return self.__get_label_tags_dict('include_tags')

    def get_exclude_tags(self) -> {}:
        return self.__get_label_tags_dict('exclude_tags')

    # --------------------------- Private ---------------------------

    def __set_label_tags_str(self, key: str, ltags_str: [str]):
        self.remove_label(key)
        self.add_tags(key, ltags_str)

    def __add_label_tags_str(self, key: str, ltag_str: str):
        self.add_tags(key, ltag_str)

    def __get_label_tags_dict(self, key: str) -> {}:
        parser = LabelTagParser()
        label_tags = self.get_tags(key)
        if parser.parse('; '.join(label_tags)):
            label_tags_list = parser.get_label_tags()
            return LabelTagParser.label_tags_list_to_dict(label_tags_list)
        else:
            return {}

    @staticmethod
    def __check_tags_str(ltags_str: [str]) -> bool:
        if not isinstance(ltags_str, (list, tuple)):
            ltags_str = [ltags_str]
        for ltag_str in ltags_str:
            if not LabelTagParser().parse(ltag_str):
                return False
        return True


# ---------------------------------------------------- FilterEditor ----------------------------------------------------

class FilterEditor(QWidget):
    def __init__(self, parent: QWidget = None):
        super(FilterEditor, self).__init__(parent)

        self.__history = None

        self.__sources = []
        self.__includes = []
        self.__excludes = []

        self.__combo_focus = QComboBox()
        self.__list_source = EasyQListSuite()
        self.__list_include = EasyQListSuite()
        self.__list_exclude = EasyQListSuite()

        self.__button_save_filter = QPushButton('Save')
        self.__button_load_filter = QPushButton('Load')
        self.__button_check_match = QPushButton('Check')
        self.__button_gen_index = QPushButton('Generate Index')

        self.__init_ui()
        self.__config_ui()

    def get_filter(self):
        pass

    def set_filter(self):
        pass

    def set_history_core(self, history: History):
        self.__history = history

    # --------------------------------------------- Private ---------------------------------------------

    def __init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        group, layout = create_v_group_box('Source Selector')
        layout.addWidget(self.__list_source)
        main_layout.addWidget(group)

        group_in, layout_in = create_v_group_box('Include Label Tags')
        group_ex, layout_ex = create_v_group_box('Exclude Label Tags')
        layout_in.addWidget(self.__list_include)
        layout_ex.addWidget(self.__list_exclude)
        main_layout.addLayout(horizon_layout([group_in, group_ex]))

        group, layout = create_v_group_box('Focus Label')
        layout.addWidget(self.__combo_focus)
        main_layout.addWidget(group)

        main_layout.addLayout(horizon_layout([self.__button_save_filter,
                                              self.__button_load_filter,
                                              self.__button_check_match,
                                              self.__button_gen_index]))

    def __config_ui(self):
        self.__combo_focus.setEditable(True)
        self.__combo_focus.addItem('')
        self.__combo_focus.addItem('event')
        self.__combo_focus.addItem('people')
        self.__combo_focus.addItem('location')
        self.__combo_focus.addItem('organization')

        self.__list_source.set_add_handler(self.__on_source_add)
        self.__list_source.set_remove_handler(self.__on_source_remove)

        self.__list_include.set_add_handler(self.__on_include_add)
        self.__list_include.set_remove_handler(self.__on_include_remove)

        self.__list_exclude.set_add_handler(self.__on_exclude_add)
        self.__list_exclude.set_remove_handler(self.__on_exclude_remove)

        self.__button_save_filter.clicked.connect(self.__on_btn_click_save)
        self.__button_load_filter.clicked.connect(self.__on_btn_click_load)
        self.__button_check_match.clicked.connect(self.__on_btn_click_chk)
        self.__button_gen_index.clicked.connect(self.__on_btn_click_gen)

    # ---------------------------------------------------------------

    def __on_source_add(self):
        root_path = HistoricalRecordLoader.get_local_depot_root()
        fname, ftype = QFileDialog.getOpenFileNames(self,
                                                    'Select History Files',
                                                    root_path,
                                                    'History Files (*.his)')
        fname = [f[len(root_path):] if f.startswith(root_path) else f for f in fname]
        self.__sources.extend(fname)
        self.__sources = list(set(self.__sources))
        self.__list_source.update_item([(s, s) for s in self.__sources])

    def __on_source_remove(self):
        items = self.__list_source.get_select_items()
        for item in items:
            self.__sources.remove(item)
        self.__list_source.update_item([(s, s) for s in self.__sources])

    def __on_include_add(self):
        text, ok = QInputDialog.getText(self, 'Include Tags', 'Include: ', QLineEdit.Normal, '')
        if not ok:
            return
        self.__includes.append(text)
        self.__includes = list(set(self.__includes))
        self.__list_include.update_item([(s, s) for s in self.__includes])

    def __on_include_remove(self):
        items = self.__list_include.get_select_items()
        for item in items:
            self.__includes.remove(item)
        self.__list_include.update_item([(s, s) for s in self.__includes])

    def __on_exclude_add(self):
        text, ok = QInputDialog.getText(self, 'Exclude Tags', 'Exclude: ', QLineEdit.Normal, '')
        if not ok:
            return
        self.__excludes.append(text)
        self.__excludes = list(set(self.__excludes))
        self.__list_exclude.update_item([(s, s) for s in self.__excludes])

    def __on_exclude_remove(self):
        items = self.__list_exclude.get_select_items()
        for item in items:
            self.__excludes.remove(item)
        self.__list_exclude.update_item([(s, s) for s in self.__excludes])

    # ---------------------------------------------------------------

    def __on_btn_click_save(self):
        fileName_choose, filetype = QFileDialog.getSaveFileName(self,
                                                                'Save Filter',
                                                                HistoricalRecordLoader.get_local_depot_root(),
                                                                'Filter Files (*.hisfilter)')
        if fileName_choose == '':
            return

        his_filter = self.ui_to_filter()
        text = his_filter.dump_text()

        with open(fileName_choose, 'wt') as f:
            f.write(text)

    def __on_btn_click_load(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                                                'Load Filter',
                                                                HistoricalRecordLoader.get_local_depot_root(),
                                                                'Filter Files (*.hisfilter)')
        if fileName_choose == '':
            return

        with open(fileName_choose, 'rt') as f:
            text = f.read()

        parser = LabelTagParser()
        if not parser.parse(text):
            print('Load from (' + fileName_choose + ') failed.')
            return

        his_filter = HistoricalFilter()
        his_filter.attach(parser.get_label_tags())

        self.filter_to_ui(his_filter)

    def __on_btn_click_chk(self):
        pass

    def __on_btn_click_gen(self):
        fileName_choose, filetype = QFileDialog.getSaveFileName(self,
                                                                'Generate Index',
                                                                HistoricalRecordLoader.get_local_depot_root(),
                                                                'Filter Files (*.index)')
        if fileName_choose == '':
            return

        records = self.load_filter_records()
        indexer = HistoricalRecordIndexer()
        indexer.index_records(records)
        indexer.dump_to_file(fileName_choose)

        QMessageBox.information(self, 'Generate Done', 'Generate index for ' + str(len(records)) + ' records Done.')

    # ---------------------------------------------------------------

    def filter_to_ui(self, his_filter: HistoricalFilter):
        self.__combo_focus.setCurrentText(his_filter.get_focus_label())

        self.__sources = his_filter.get_sources()
        self.__includes = self.__label_tag_dict_to_text(his_filter.get_include_tags())
        self.__excludes = self.__label_tag_dict_to_text(his_filter.get_exclude_tags())

        self.__list_source.update_item([(s, s) for s in self.__sources])
        self.__list_include.update_item([(s, s) for s in self.__includes])
        self.__list_exclude.update_item([(s, s) for s in self.__excludes])

    def ui_to_filter(self) -> HistoricalFilter:
        his_filter = HistoricalFilter()
        his_filter.set_sources(self.__sources)
        his_filter.set_focus_label(self.__combo_focus.currentText())
        his_filter.set_include_tags_str(self.__includes)
        his_filter.set_exclude_tags_str(self.__excludes)
        return his_filter

    def load_source_records(self) -> [HistoricalRecord]:
        records = []
        for source in self.__sources:
            loader = HistoricalRecordLoader()
            if path.isabs(source):
                ret = loader.from_file(source)
            else:
                ret = loader.from_source(source)
            if not ret:
                continue
            records.extend(loader.get_loaded_records())
        return records

    def load_filter_records(self) -> [HistoricalRecord]:
        history = self.__history if self.__history is not None else History()

        records = self.load_source_records()
        history.set_records(records)

        his_filter = self.ui_to_filter()
        return history.select_records(sources=his_filter.get_sources(),
                                      focus_label=his_filter.get_focus_label(),
                                      include_label_tags=his_filter.get_include_tags(), include_all=False,
                                      exclude_label_tags=his_filter.get_exclude_tags(), exclude_any=True)

    def __label_tag_dict_to_text(self, label_tags_dict: dict):
        return [key + ': ' + ', '.join(label_tags_dict[key]) for key in label_tags_dict.keys()]


# -------------------------------------------------------  Test --------------------------------------------------------

def test_historical_filter():
    his_filter = HistoricalFilter()

    his_filter.set_sources(['/a/b/c',
                            'D:\\abc',
                            'test.his'])
    his_filter.set_focus_label('people')

    assert his_filter.add_include_tags_str('include_1')
    assert his_filter.add_include_tags_str('include_2: inc_tag1, inc_tag2')
    assert his_filter.add_include_tags_str('include_3: ')

    assert his_filter.add_exclude_tags_str('exclude_1')
    assert his_filter.add_exclude_tags_str('exclude_2: exc_tag1, exc_tag2')
    assert his_filter.add_exclude_tags_str('exclude_3: ')

    text = his_filter.dump_text()
    print(text)

    parser = LabelTagParser()
    if not parser.parse(text):
        print('Load from dump text failed.')
        assert False

    his_filter = HistoricalFilter()
    his_filter.attach(parser.get_label_tags())

    sources = his_filter.get_sources()
    focus_label = his_filter.get_focus_label()
    include_ltags = his_filter.get_include_tags()
    exclude_ltags = his_filter.get_exclude_tags()

    assert '/a/b/c' in sources
    assert 'D:\\abc' in sources
    assert 'test.his' in sources

    assert focus_label == 'people'

    assert 'include_1' in include_ltags.keys()
    assert 'include_2' in include_ltags.keys()
    assert 'include_3' in include_ltags.keys()

    assert 'inc_tag1' in include_ltags['include_2']
    assert 'inc_tag2' in include_ltags['include_2']

    assert 'exclude_1' in exclude_ltags.keys()
    assert 'exclude_2' in exclude_ltags.keys()
    assert 'exclude_3' in exclude_ltags.keys()

    assert 'exc_tag1' in exclude_ltags['exclude_2']
    assert 'exc_tag2' in exclude_ltags['exclude_2']

    assert(focus_label == 'people')


def test_historical_filter_ui():
    app = QApplication(sys.argv)
    wnd = FilterEditor()
    wnd.showNormal()
    app.exec_()


# ------------------------------------------------ File Entry : main() -------------------------------------------------

def main():
    test_historical_filter()
    test_historical_filter_ui()


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






