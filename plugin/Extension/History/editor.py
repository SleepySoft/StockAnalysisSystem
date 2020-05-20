import traceback

from PyQt5.QtWidgets import QLineEdit, QAbstractItemView, QFileDialog, QCheckBox, QWidget, QLabel, QTextEdit, \
    QTabWidget, QComboBox, QGridLayout, QRadioButton, QListWidget, QListWidgetItem, QInputDialog

from .core import *
from .Utility.ui_utility import *


# ---------------------------------------------- class HistoryRecordEditor ---------------------------------------------

class HistoryRecordEditor(QWidget):

    class Agent:
        def __init__(self):
            pass

        def on_apply(self):
            pass

        def on_cancel(self):
            pass

    def __init__(self, parent: QWidget):
        super(HistoryRecordEditor, self).__init__(parent)

        self.__records = []
        self.__source = ''
        self.__current_record = None
        self.__operation_agents = []

        self.__ignore_combo = False

        self.__tab_main = QTabWidget()
        self.__current_depot = 'default'
        # self.__combo_depot = QComboBox()
        self.__combo_records = QComboBox()

        self.__label_uuid = QLabel()
        self.__label_source = QLabel()
        self.__line_time = QLineEdit()
        self.__line_location = QLineEdit()
        self.__line_people = QLineEdit()
        self.__line_organization = QLineEdit()
        self.__line_default_tags = QLineEdit()

        self.__button_auto_time = QPushButton('Auto Detect')
        self.__button_auto_location = QPushButton('Auto Detect')
        self.__button_auto_people = QPushButton('Auto Detect')
        self.__button_auto_organization = QPushButton('Auto Detect')

        self.__radio_time = QRadioButton('Time')
        self.__radio_location = QRadioButton('Location')
        self.__radio_people = QRadioButton('Participant')
        self.__radio_organization = QRadioButton('Organization')
        self.__radio_record = QRadioButton('Event')

        self.__check_time = QCheckBox('Lock')
        self.__check_location = QCheckBox('Lock')
        self.__check_people = QCheckBox('Lock')
        self.__check_organization = QCheckBox('Lock')
        self.__check_default_tags = QCheckBox('Lock')

        self.__line_title = QLineEdit()
        self.__text_brief = QTextEdit()
        self.__text_record = QTextEdit()

        self.__table_tags = EasyQTableWidget()

        self.__button_new = QPushButton('New Event')
        self.__button_new_file = QPushButton('New File')
        self.__button_del = QPushButton('Del Event')
        self.__button_apply = QPushButton('Apply')
        self.__button_cancel = QPushButton('Cancel')

        self.init_ui()
        self.config_ui()

    def init_ui(self):
        root_layout = QVBoxLayout()

        line = QHBoxLayout()
        # line.addWidget(QLabel('Event Source'), 0)
        line.addWidget(self.__label_source, 1)
        line.addWidget(self.__button_new_file, 0)
        root_layout.addLayout(line)

        line = QHBoxLayout()
        line.addWidget(self.__combo_records, 1)
        line.addWidget(self.__button_new, 0)
        line.addWidget(self.__button_del, 0)
        root_layout.addLayout(line)

        root_layout.addWidget(self.__tab_main)
        root_layout.addLayout(horizon_layout([self.__button_apply, self.__button_cancel]))
        self.setLayout(root_layout)

        record_page_layout = create_new_tab(self.__tab_main, 'Event Editor')

        property_layout = QGridLayout()

        row = 0
        property_layout.addWidget(QLabel('Event ID'), row, 0)
        property_layout.addWidget(self.__label_uuid, row, 1)

        row += 1
        property_layout.addWidget(QLabel('Event Tags'), row, 0)
        property_layout.addWidget(self.__line_default_tags, row, 1, 1, 2)
        property_layout.addWidget(self.__check_default_tags, row, 3)

        row += 1
        # property_layout.addWidget(QLabel('Event Time'), 1, 0)
        property_layout.addWidget(self.__radio_time, row, 0)
        property_layout.addWidget(self.__line_time, row, 1)
        property_layout.addWidget(self.__button_auto_time, row, 2)
        property_layout.addWidget(self.__check_time, row, 3)

        row += 1
        # property_layout.addWidget(QLabel('Event Location'), 2, 0)
        property_layout.addWidget(self.__radio_location, row, 0)
        property_layout.addWidget(self.__line_location, row, 1)
        property_layout.addWidget(self.__button_auto_location, row, 2)
        property_layout.addWidget(self.__check_location, row, 3)

        row += 1
        # property_layout.addWidget(QLabel('Event Participant'), 3, 0)
        property_layout.addWidget(self.__radio_people, row, 0)
        property_layout.addWidget(self.__line_people, row, 1)
        property_layout.addWidget(self.__button_auto_people, row, 2)
        property_layout.addWidget(self.__check_people, row, 3)

        row += 1
        # property_layout.addWidget(QLabel('Event Organization'), 4, 0)
        property_layout.addWidget(self.__radio_organization, row, 0)
        property_layout.addWidget(self.__line_organization, row, 1)
        property_layout.addWidget(self.__button_auto_organization, row, 2)
        property_layout.addWidget(self.__check_organization, row, 3)

        row += 1
        self.__radio_record.setChecked(True)
        property_layout.addWidget(self.__radio_record, row, 0)

        record_page_layout.addLayout(property_layout)

        group, layout = create_v_group_box('')
        record_page_layout.addWidget(group)

        layout.addWidget(QLabel('Event Title'))
        layout.addWidget(self.__line_title)

        layout.addWidget(QLabel('Event Brief'))
        layout.addWidget(self.__text_brief, 2)

        layout.addWidget(QLabel('Event Description'))
        layout.addWidget(self.__text_record, 5)

        layout = create_new_tab(self.__tab_main, 'Label Tag Editor')
        layout.addWidget(self.__table_tags)

        self.setMinimumSize(700, 500)

    def config_ui(self):
        self.__button_auto_time.clicked.connect(self.on_button_auto_time)
        self.__button_auto_location.clicked.connect(self.on_button_auto_location)
        self.__button_auto_people.clicked.connect(self.on_button_auto_people)
        self.__button_auto_organization.clicked.connect(self.on_button_auto_organization)

        self.__button_new.clicked.connect(self.on_button_new)
        self.__button_new_file.clicked.connect(self.on_button_file)
        self.__button_del.clicked.connect(self.on_button_del)
        self.__button_apply.clicked.connect(self.on_button_apply)
        self.__button_cancel.clicked.connect(self.on_button_cancel)

        self.__combo_records.currentIndexChanged.connect(self.on_combo_records)

    def update_combo_records(self):
        index = -1
        self.__ignore_combo = True
        self.__combo_records.clear()

        sorted_records = History.sort_records(self.__records)

        for i in range(0, len(sorted_records)):
            record = sorted_records[i]
            self.__combo_records.addItem('[' + HistoryTime.tick_to_standard_string(record.since()) + '] ' +
                                         record.uuid())
            self.__combo_records.setItemData(i, record.uuid())
            if record == self.__current_record:
                index = i
        self.__ignore_combo = False

        if index >= 0:
            self.__combo_records.setCurrentIndex(index)
            self.on_combo_records()
        else:
            if self.__combo_records.count() > 0:
                self.__combo_records.setCurrentIndex(0)
                self.on_combo_records()
            print('Cannot find the current record in combobox - use index 0.')

    # ---------------------------------------------------- Features ----------------------------------------------------

    def add_agent(self, agent):
        self.__operation_agents.append(agent)

    def set_current_depot(self, depot: str):
        self.__current_depot = depot
        print('| Editor current depot: ' + depot)

    def set_current_source(self, source: str):
        self.__source = source
        print('Editor current source: ' + source)

    def edit_source(self, source: str, current_uuid: str = '') -> bool:
        # TODO: Do we need this?
        loader = HistoricalRecordLoader()
        if not loader.from_source(source):
            return False
        self.set_current_source(source)
        self.__records = loader.get_loaded_records()
        self.__current_record = None

        for record in self.__records:
            if current_uuid is None or current_uuid == '' or record.uuid() == current_uuid:
                self.__current_record = record
                break

        if self.__current_record is None:
            self.__current_record = HistoricalRecord()
        self.update_combo_records()
        self.record_to_ui(self.__current_record)

    def set_records(self, records: HistoricalRecord or [HistoricalRecord], source: str):
        self.__records = records if isinstance(records, list) else [records]
        self.__current_record = self.__records[0]
        self.set_current_source(source)
        self.update_combo_records()

    def get_source(self) -> str:
        return self.__source

    def get_records(self) -> [HistoricalRecord]:
        return self.__records

    def get_current_record(self) -> HistoricalRecord:
        return self.__current_record

    # ---------------------------------------------------- UI Event ----------------------------------------------------

    def on_button_auto_time(self):
        pass

    def on_button_auto_location(self):
        pass

    def on_button_auto_people(self):
        pass

    def on_button_auto_organization(self):
        pass

    def on_button_new(self):
        self.create_new_record()

    def on_button_file(self):
        self.create_new_file()

    def on_button_del(self):
        if self.__current_record in self.__records:
            self.__records.remove(self.__current_record)
        self.__current_record = None
        self.update_combo_records()

    def on_button_apply(self):
        if self.__current_record is None:
            self.__current_record = HistoricalRecord()
            self.__records.append(self.__current_record)
        else:
            self.__current_record.reset()

        if not self.ui_to_record(self.__current_record):
            return

        for agent in self.__operation_agents:
            agent.on_apply()

    def on_button_cancel(self):
        for agent in self.__operation_agents:
            agent.on_cancel()

    def on_combo_records(self):
        if self.__ignore_combo:
            return

        _uuid = self.__combo_records.currentData()
        record = self.__look_for_record(_uuid)

        if record is None:
            print('Cannot find record for uuid: ' + _uuid)
            return

        self.__current_record = record
        self.record_to_ui(record)

    # --------------------------------------------------- Operation ----------------------------------------------------

    def clear_ui(self):
        lock_time = self.__check_time.isChecked()
        lock_location = self.__check_location.isChecked()
        lock_people = self.__check_people.isChecked()
        lock_organization = self.__check_organization.isChecked()
        lock_default_tags = self.__check_default_tags.isChecked()

        self.__label_uuid.setText('')
        self.__label_source.setText('')

        if not lock_time:
            self.__line_time.setText('')
        if not lock_location:
            self.__line_location.setText('')
        if not lock_people:
            self.__line_people.setText('')
        if not lock_organization:
            self.__line_organization.setText('')
        if not lock_default_tags:
            self.__line_default_tags.setText('')

        self.__line_title.clear()
        self.__text_brief.clear()
        self.__text_record.clear()

        restore_text_editor(self.__text_brief)
        restore_text_editor(self.__text_record)

    def ui_to_record(self, record: HistoricalRecord) -> bool:
        input_time = self.__line_time.text()
        input_location = self.__line_location.text()
        input_people = self.__line_people.text()
        input_organization = self.__line_organization.text()
        input_default_tags = self.__line_default_tags.text()

        input_title = self.__line_title.text()
        input_brief = self.__text_brief.toPlainText()
        input_event = self.__text_record.toPlainText()

        focus_time = self.__radio_time.isChecked()
        focus_location = self.__radio_location.isChecked()
        focus_poeple = self.__radio_people.isChecked()
        focus_organization = self.__radio_organization.isChecked()
        focus_record = self.__radio_record.isChecked()

        focus_label = ''
        input_valid = False

        if focus_time:
            focus_label = 'time'
            input_valid = (len(input_time.strip()) != 0)
        if focus_location:
            focus_label = 'location'
            input_valid = (len(input_location.strip()) != 0)
        if focus_poeple:
            focus_label = 'people'
            input_valid = (len(input_people.strip()) != 0)
        if focus_organization:
            focus_label = 'organization'
            input_valid = (len(input_organization.strip()) != 0)
        if focus_record:
            focus_label = 'event'
            input_valid = (len(input_title.strip()) != 0 or
                           len(input_brief.strip()) != 0 or
                           len(input_event.strip()) != 0)
        if not input_valid:
            tips = 'The focus label you select is: ' + focus_label + ".\n\nBut you didn't put content in it."
            QMessageBox.information(None, 'Save', tips, QMessageBox.Ok)
            return False

        record.set_label_tags('time',         input_time.split(','))
        record.set_label_tags('location',     input_location.split(','))
        record.set_label_tags('people',       input_people.split(','))
        record.set_label_tags('organization', input_organization.split(','))
        record.set_label_tags('tags',         input_default_tags.split(','))

        record.set_label_tags('title', input_title)
        record.set_label_tags('brief', input_brief)
        record.set_label_tags('event', input_event)

        record.set_focus_label(focus_label)

        return True

    def record_to_ui(self, record: HistoricalRecord or str):
        self.clear_ui()

        self.__label_uuid.setText(LabelTagParser.tags_to_text(record.uuid()))
        self.__label_source.setText(self.__source)
        self.__line_time.setText(LabelTagParser.tags_to_text(record.time()))

        self.__line_location.setText(LabelTagParser.tags_to_text(record.get_tags('location')))
        self.__line_people.setText(LabelTagParser.tags_to_text(record.get_tags('people')))
        self.__line_organization.setText(LabelTagParser.tags_to_text(record.get_tags('organization')))
        self.__line_default_tags.setText(LabelTagParser.tags_to_text(record.get_tags('tags')))

        self.__line_title.setText(LabelTagParser.tags_to_text(record.title()))
        self.__text_brief.setText(LabelTagParser.tags_to_text(record.brief()))
        self.__text_record.setText(LabelTagParser.tags_to_text(record.event()))

    def create_new_record(self):
        if self.__current_record is not None:
            # TODO:
            pass
        self.__new_record()

        self.clear_ui()
        self.update_combo_records()
        self.__label_uuid.setText(LabelTagParser.tags_to_text(self.__current_record.uuid()))
        self.__label_source.setText(self.__source)

    def create_new_file(self):
        self.__new_file()

        self.clear_ui()
        self.update_combo_records()
        self.__label_uuid.setText(LabelTagParser.tags_to_text(self.__current_record.uuid()))
        self.__label_source.setText(self.__source)

        # self.__source = path.join(self.__current_depot, str(self.__current_record.uuid()) + '.his')
        # self.__records.clear()
        # self.create_new_record()

    # def save_records(self):
    #     result = History.Loader().to_local_depot(self.__records, 'China', self.__source)
    #     tips = 'Save Successful.' if result else 'Save Fail.'
    #     tips += '\nSave File: ' + self.__source
    #     QMessageBox.information(None, 'Save', tips, QMessageBox.Ok)

    # ------------------------------------------------------------------------------

    def __new_file(self):
        self.__records.clear()
        self.set_current_source('')
        self.__new_record()

    def __new_record(self):
        self.__current_record = HistoricalRecord()
        self.__records.append(self.__current_record)
        if self.__source is None or self.__source == '':
            self.__source = path.join(self.__current_depot, str(self.__current_record.uuid()) + '.his')
            self.set_current_source(self.__source)
        self.__current_record.set_source(self.__source)

    def __look_for_record(self, _uuid: str):
        for record in self.__records:
            if record.uuid() == _uuid:
                return record
        return None


# --------------------------------------------- class HistoryRecordBrowser ---------------------------------------------

class HistoryRecordBrowser(QWidget):

    class Agent:
        def __init__(self):
            pass

        def on_select_depot(self, depot: str):
            pass

        def on_select_record(self, record: str):
            pass

    def __init__(self, parent: QWidget):
        super(HistoryRecordBrowser, self).__init__(parent)

        self.__ignore_combo = False
        self.__current_file = ''
        self.__current_depot = 'default'
        self.__operation_agents = []

        self.__combo_depot = QComboBox()
        self.__list_record = QListWidget()
        self.__button_rename = QPushButton('Rename')

        self.init_ui()
        self.config_ui()

    def init_ui(self):
        root_layout = QVBoxLayout()
        self.setLayout(root_layout)

        root_layout.addWidget(self.__combo_depot, 0)
        root_layout.addWidget(self.__list_record, 10)
        root_layout.addWidget(self.__button_rename, 0)

    def config_ui(self):
        self.setMinimumWidth(200)
        self.update_combo_depot()
        self.__combo_depot.currentIndexChanged.connect(self.on_combo_depot_changed)
        self.__list_record.selectionModel().selectionChanged.connect(self.on_list_record_changed)
        self.__button_rename.clicked.connect(self.on_button_rename)

    def add_agent(self, agent):
        self.__operation_agents.append(agent)

    def refresh(self):
        self.update_list_record(self.__current_depot)

    def get_current_depot(self):
        return self.__current_depot

    def update_combo_depot(self):
        depots = HistoryRecordBrowser.enumerate_local_depot()
        if len(depots) == 0:
            return
        self.__ignore_combo = True
        for depot in depots:
            self.__combo_depot.addItem(os.path.basename(depot), depot)
        self.__ignore_combo = False

        self.__combo_depot.setCurrentIndex(0)
        self.on_combo_depot_changed()

    def update_list_record(self, depot: str):
        record_dir_file = HistoryRecordBrowser.enumerate_depot_record(depot)

        self.__list_record.clear()
        for record_path, record_file in record_dir_file:
            item = QListWidgetItem()
            item.setText(record_file)
            item.setData(QtCore.Qt.UserRole, path.join(record_path, record_file))
            self.__list_record.addItem(item)

    def on_combo_depot_changed(self):
        if self.__ignore_combo:
            return
        depot = self.__combo_depot.currentText()
        self.update_list_record(depot)
        self.__current_depot = depot

        for agent in self.__operation_agents:
            agent.on_select_depot(depot)

    def on_list_record_changed(self):
        item = self.__list_record.currentItem()
        record_path = item.data(QtCore.Qt.UserRole)
        self.__current_file = record_path

        for agent in self.__operation_agents:
            agent.on_select_record(record_path)

    def on_button_rename(self):
        if self.__current_file is None or self.__current_file == '':
            return
        text, ok = QInputDialog.getText(self, 'Rename', 'New Name')
        if not ok:
            return
        if not text.endswith('.his'):
            text += '.his'
        new_path = os.path.join(os.path.dirname(self.__current_file), text)

        tip = 'Rename from \n"' + self.__current_file + '" \nto "' + new_path + '" '
        try:
            os.rename(self.__current_file, new_path)
            QMessageBox.information(self, 'Rename', tip + 'Successful.', QMessageBox.Ok)
            self.refresh()
        except Exception as e:
            QMessageBox.information(self, 'Rename', tip + 'Failed.', QMessageBox.Ok)
        finally:
            pass

    @staticmethod
    def enumerate_local_depot() -> list:
        depot_root = HistoricalRecordLoader.get_local_depot_root()
        items = os.listdir(depot_root)
        return [item for item in items if path.isdir(path.join(depot_root, item))]

    @staticmethod
    def enumerate_depot_record(depot: str) -> list:
        record_dir_file = []
        depot_path = HistoricalRecordLoader.join_local_depot_path(depot)
        for parent, dirnames, filenames in os.walk(depot_path):
            for filename in filenames:
                if filename.endswith('.his'):
                    record_dir_file.append((parent, filename))
        return record_dir_file


# --------------------------------------------- class HistoryEditorDialog ----------------------------------------------

class HistoryEditorDialog(QDialog):
    def __init__(self,
                 editor_agent: HistoryRecordEditor.Agent = None,
                 browser_agent: HistoryRecordBrowser.Agent = None):
        super(HistoryEditorDialog, self).__init__()

        self.__current_depot = 'default'

        self.history_editor = HistoryRecordEditor(self)
        self.history_editor.add_agent(editor_agent if editor_agent is not None else self)

        self.history_browser = HistoryRecordBrowser(self)
        self.history_browser.add_agent(browser_agent if browser_agent is not None else self)

        layout = QHBoxLayout()
        layout.addWidget(self.history_browser, 1)
        layout.addWidget(self.history_editor, 3)

        self.setLayout(layout)
        self.setWindowFlags(int(self.windowFlags()) |
                            Qt.WindowMinMaxButtonsHint |
                            QtCore.Qt.WindowSystemMenuHint)

        self.__current_depot = self.history_browser.get_current_depot()
        self.history_editor.set_current_depot(self.__current_depot)

    # def showEvent(self, event):
    #     self.setFocus()
    #     event.accept()

    def show_browser(self, show: bool = True):
        self.get_history_browser().setVisible(show)

    def get_history_editor(self) -> HistoryRecordEditor:
        return self.history_editor

    def get_history_browser(self) -> HistoryRecordBrowser:
        return self.history_browser

    # ------------------------------- HistoryRecordEditor.Agent -------------------------------

    def on_apply(self):
        source = self.history_editor.get_source()
        records = self.history_editor.get_records()

        if records is None or len(records) == 0:
            return

        if source is None or source == '':
            source = records[0].source()
        if source is None or source == '':
            source = path.join(self.__current_depot, records[0].uuid() + '.his')

        # TODO: Select depot
        # result = HistoricalRecordLoader.to_local_source(records, source)
        result = HistoricalRecordLoader.to_local_source(records, source)
        if not result:
            return

        # result = False
        # if len(self.__records) == 0:
        #     source = str(self.__current_record.uuid()) + '.his'
        # else:
        #     # The whole file should be updated
        #     if self.__current_record not in self.__records:
        #         self.__records.append(self.__current_record)
        #     source = self.__records[0].source()
        #     if source is None or len(source) == 0:
        #         source = str(self.__current_record.uuid()) + '.his'
        #         result = History.Loader().to_local_depot(self.__records, 'China', source)

        tips = 'Save Successful.' if result else 'Save Fail.'
        if len(source) > 0:
            tips += '\nSave File: ' + source
        QMessageBox.information(self, 'Save', tips, QMessageBox.Ok)

        self.history_browser.refresh()

    def on_cancel(self):
        self.close()

    # ------------------------------ HistoryRecordBrowser.Agent ------------------------------

    def on_select_depot(self, depot: str):
        self.__current_depot = depot
        self.history_editor.set_current_depot(depot)

    def on_select_record(self, record: str):
        self.history_editor.edit_source(record)


# ------------------------------------------------ File Entry : main() -------------------------------------------------

def main():
    app = QApplication(sys.argv)
    HistoryEditorDialog().exec()


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



