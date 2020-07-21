import os
import sys
import json
import traceback

root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ----------------------------------------------------- class Tags -----------------------------------------------------

class Tags:
    def __init__(self, record_path: str):
        self.__tags_path = record_path
        self.__tag_obj_dict = {}
        self.__obj_tag_dict = {}
        self.load()

    def all_tags(self) -> [str]:
        return list(self.__tag_obj_dict.keys())

    def all_objs(self) -> [str]:
        return list(self.__obj_tag_dict.keys())

    def tags_of_objs(self, objs: str or [str]) -> [str]:
        tags = []
        objs = self.__check_wrap_str(objs)
        for obj in objs:
            tags.extend(self.__obj_tag_dict.get(obj, []))
        return list(set(tags))

    def objs_from_tags(self, tags: str or [str]) -> [str]:
        objs = []
        tags = self.__check_wrap_str(tags)
        for tag in tags:
            objs.extend(self.__tag_obj_dict.get(tag, []))
        return list(set(objs))

    def set_obj_tags(self, obj: str, tags: str or [str]):
        if tags is None or tags == '':
            return
        tags = self.__check_wrap_str(tags)
        self.clear_obj_tags(obj)
        self.__obj_tag_dict[obj] = tags
        for tag in tags:
            tag = tag.strip()
            if tag == '':
                continue
            obj_valid = obj is not None and obj != ''
            if tag not in self.__tag_obj_dict:
                self.__tag_obj_dict[tag] = [obj] if obj_valid else []
            elif obj_valid and obj not in self.__tag_obj_dict[tag]:
                self.__tag_obj_dict[tag].append(obj)

    def clear_obj_tags(self, obj: str):
        if obj in self.__obj_tag_dict.keys():
            tags = self.__obj_tag_dict.get(obj, [])
            del self.__obj_tag_dict[obj]
            self.__remove_obj_from_tag_obj_dict(obj, tags)

    def add_obj_tags(self, obj: str, tags: str or [str]):
        if tags is None or tags == '':
            return
        tags = self.__check_wrap_str(tags)
        exists_tags = self.tags_of_objs(obj)
        combined_tags = list(set(exists_tags + tags))
        self.set_obj_tags(obj, combined_tags)

    def remove_obj_tags(self, obj: str, tags: str or [str]):
        if tags is None or tags == '':
            return
        tags = self.__check_wrap_str(tags)
        exists_tags = self.tags_of_objs(obj)
        combined_tags = list(set(exists_tags).difference(set(tags)))
        self.set_obj_tags(obj, combined_tags)

    def save(self, record_path: str = ''):
        if record_path != '':
            if self.__save(record_path):
                self.__tags_path = record_path
                return True
            else:
                return False
        return self.__save(self.__tags_path)

    def load(self, record_path: str = '') -> bool:
        if record_path != '':
            if self.__load(record_path):
                self.__tags_path = record_path
                return True
            else:
                return False
        return self.__load(self.__tags_path)

    # -------------------------------------------------------------------------------------------

    def __save(self, record_path: str) -> bool:
        try:
            with open(record_path, 'wt') as f:
                json.dump(self.__tag_obj_dict, f, indent=4)
            return True
        except Exception as e:
            print('Save tags fail.')
            print(e)
            print(traceback.format_exc())
            return False
        finally:
            pass

    def __load(self, record_path: str) -> bool:
        self.__obj_tag_dict.clear()
        self.__tag_obj_dict.clear()
        try:
            with open(record_path, 'rt') as f:
                self.__obj_tag_dict.clear()
                self.__tag_obj_dict = json.load(f)
                self.__build_obj_tag_dict_from_tag_obj_dict()
            return True
        except Exception as e:
            print('Load tags fail.')
            print(e)
            print(traceback.format_exc())
            return False
        finally:
            pass

    def __remove_obj_from_tag_obj_dict(self, obj: str, tags: list or None = None):
        if tags is None:
            tags = list(self.__tag_obj_dict.keys())
        for tag in tags:
            obj_list = self.__tag_obj_dict.get(tag, [])
            if obj in obj_list:
                obj_list.remove(obj)

    def __build_obj_tag_dict_from_tag_obj_dict(self):
        for tag, objs in self.__tag_obj_dict.items():
            for obj in objs:
                if obj not in self.__obj_tag_dict.keys():
                    self.__obj_tag_dict[obj] = [tag]
                else:
                    self.__obj_tag_dict[obj].append(tag)

    @staticmethod
    def tags_to_str(tags: str or [str]) -> str:
        return '; '.join(tags)

    @staticmethod
    def str_to_tags(text: str) -> [str]:
        return [tag.strip() for tag in text.split(';')] if text.strip() != '' else []

    @staticmethod
    def __check_wrap_str(tags: str or [str]) -> [str]:
        return tags if isinstance(tags, (list, tuple)) else [tags]


# ----------------------------------------------------- class Tags -----------------------------------------------------

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, QDateTime, QPoint, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QButtonGroup, QDateTimeEdit, QApplication, QLabel, QTextEdit, QPushButton, QVBoxLayout, \
    QMessageBox, QWidget, QComboBox, QCheckBox, QRadioButton, QLineEdit, QAbstractItemView, QScrollArea

from StockAnalysisSystem.core.Utiltity.ui_utility import *
from StockAnalysisSystem.core.Utiltity.FlowLayout import FlowLayout


class TagsUi(QScrollArea):
    def __init__(self, tags: Tags):
        self.__tags = tags
        super(TagsUi, self).__init__()

        self.__check_tags = []
        self.__loaded_tags = []

        self.__line_tags = QLineEdit()
        self.__flow_layout = FlowLayout()
        self.__button_ensure = QPushButton('OK')

        self.init_ui()
        self.reload_tags()

    def init_ui(self):
        container = QWidget()
        container_layout = QVBoxLayout()
        self.__flow_layout.heightChanged.connect(container.setMinimumHeight)

        group_box = QGroupBox('Tags')
        group_box.setLayout(self.__flow_layout)

        container_layout.addWidget(group_box, 99)
        container_layout.addLayout(horizon_layout([
            QLabel("Other tags (separate by ';')"),
            self.__line_tags, self.__button_ensure], [1, 99, 1]))

        container_layout.addStretch()
        container.setLayout(container_layout)

        self.setWindowTitle('Tags')
        self.setWidgetResizable(True)
        self.setWidget(container)

        self.setMinimumSize(650, 400)

    def __create_check_box_for_tag(self, tag: str):
        check_box = QCheckBox(tag)
        # check_box.clicked.connect(self.__on_checkbox_clicked())
        self.__flow_layout.addWidget(check_box)
        self.__check_tags.append(check_box)

    # Dynamic update is too complex
    # def __on_checkbox_clicked(self):
    #     input_tags = Tags.str_to_tags(self.__line_tags)
    #     tags = Tags.str_to_tags(input_tags)

    # ---------------------------------------------------------------------

    def on_ensure(self, func):
        self.__button_ensure.clicked.connect(func)

    def empty_tags(self):
        # https://stackoverflow.com/a/10067548
        while self.__flow_layout.count() > 0:
            child = self.__flow_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.__check_tags.clear()
        self.__loaded_tags.clear()
        self.__line_tags.setText('')

    def reload_tags(self):
        self.empty_tags()
        tags = self.__tags.all_tags()
        for tag in sorted(tags):
            self.__create_check_box_for_tag(tag)
        self.__loaded_tags = tags
        self.__flow_layout.update()

    def select_tags(self, tags: [str]):
        for tag in tags:
            if tag not in self.__loaded_tags:
                self.__create_check_box_for_tag(tag)
                self.__loaded_tags.append(tag)
        for check_box in self.__check_tags:
            check_box.setChecked(check_box.text() in tags)
        self.__flow_layout.update()

    def get_selected_tags(self):
        input_tags = Tags.str_to_tags(self.__line_tags.text())
        select_tags = [check_box.text() for check_box in self.__check_tags if check_box.isChecked()]
        return list(set(input_tags + select_tags))


# ----------------------------------------------------------------------------------------------------------------------

def __verify_basic_test(tags: Tags, test_table: dict) -> bool:
    all_tags = []
    for obj, tag in test_table.items():
        all_tags.extend(tag)
    all_tags = list(set(all_tags))

    for obj, tag in test_table.items():
        obj_tags = tags.tags_of_objs(obj)
        assert sorted(obj_tags) == sorted(tag)

    assert sorted(tags.all_objs()) == sorted(list(test_table.keys()))
    assert sorted(tags.all_tags()) == sorted(all_tags)

    assert sorted(tags.objs_from_tags('E')) == sorted(['ObjA', 'ObjB', 'ObjC'])
    assert sorted(tags.objs_from_tags(['A', 'I'])) == sorted(['ObjA', 'ObjD'])

    return True


TAGS = None


def test_basic():
    test_table = {
        'ObjA': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
        'ObjB': ['E', 'F', 'G', 'H'],
        'ObjC': ['B', 'C', 'D', 'E'],
        'ObjD': ['F', 'G', 'H', 'I']
    }

    tags = Tags(os.path.join(root_path, 'TestData', 'tags.json'))

    for obj, tag in test_table.items():
        tags.set_obj_tags(obj, tag)
    assert __verify_basic_test(tags, test_table)
    assert tags.save()

    tags = Tags(os.path.join(root_path, 'TestData', 'tags.json'))
    assert tags.load()
    assert __verify_basic_test(tags, test_table)

    tags.add_obj_tags('ObjA', ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'])
    assert sorted(tags.tags_of_objs('ObjA')) == sorted(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'])

    tags.remove_obj_tags('ObjA', ['A', 'C', 'E', 'G', 'I'])
    assert sorted(tags.tags_of_objs('ObjA')) == sorted(['B', 'D', 'F', 'H'])

    tags.add_obj_tags('ObjE', 'X')
    tags.add_obj_tags('ObjE', 'XY')
    tags.add_obj_tags('ObjE', 'XYZ')
    assert sorted(tags.tags_of_objs('ObjE')) == sorted(['X', 'XY', 'XYZ'])

    tags.remove_obj_tags('ObjE', 'X')
    tags.remove_obj_tags('ObjE', 'Y')
    tags.remove_obj_tags('ObjE', 'Z')
    assert sorted(tags.tags_of_objs('ObjE')) == sorted(['XY', 'XYZ'])

    global TAGS
    TAGS = tags


def test_entry():
    test_basic()


# ----------------------------------------------------------------------------------------------------------------------

def tags_ensure(tags_ui: TagsUi):
    tags = tags_ui.get_selected_tags()
    QMessageBox.information(None, 'Select Tags', Tags.tags_to_str(tags))
    # tags_ui.close()
    # exit(0)


def main():
    test_entry()

    app = QApplication(sys.argv)
    w = TagsUi(TAGS)
    w.on_ensure(partial(tags_ensure, w))
    w.reload_tags()
    w.select_tags(['A', 'C', 'E'])
    w.show()
    sys.exit(app.exec_())


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







