import os
import re
import math
import time
import uuid
import ntpath
from functools import total_ordering

import requests
import traceback
import posixpath
from os import sys, path, listdir

from .Utility.to_arab import *
from .Utility.history_time import *
from .Utility.history_public import *


# ---------------------------------------------------- Token Parser ----------------------------------------------------

class TokenParser:
    def __init__(self):
        self.__text = ''
        self.__tokens = []
        self.__wrappers = []                  # [(start, close)]
        self.__space_tokens = [' ']
        self.__escape_symbols = ['\\']

        self.__mark_idx = 0
        self.__parse_idx = 0

        self.__meet_token = ''

        self.__in_wrapper = False
        self.__wrapper_index = -1

    # ========================================== Config parser ==========================================

    def config(self, tokens: list, wrappers: list, escape_symbols: list):
        self.__tokens = tokens
        self.__wrappers = wrappers
        self.__escape_symbols = escape_symbols

        for wrapper in wrappers:
            if not isinstance(wrapper, (list, tuple)) or len(wrapper) != 2:
                print('! Error wrapper format. Its format should be: [(start, close)], ...')
            for token in wrapper:
                if token not in self.__tokens:
                    self.__tokens.append(token)

    def reset(self):
        self.__mark_idx = 0
        self.__parse_idx = 0

        self.__in_wrapper = False
        self.__wrapper_index = -1

    def attach(self, text: str):
        self.__text = text
        self.__mark_idx = 0
        self.__parse_idx = 0

    # ========================================== Parse ==========================================

    def next_token(self) -> str:
        while not self.reaches_end():
            if self.__meet_token != '':
                token = self.__meet_token
                self.__meet_token = ''
                self.offset(len(token))
                if token not in self.__space_tokens:
                    break
                else:
                    self.yield_str()
                    continue
            elif self.__in_wrapper:
                expect_close = self.__wrappers[self.__wrapper_index][1]
                if not self.offset_until(expect_close):
                    break
                if not self.__check_escape_symbol():
                    self.__in_wrapper = False
                    self.__meet_token = expect_close
                    break
            else:
                self.__meet_token = self.__check_meet_token()
                if self.__meet_token != '':
                    break
            self.offset(1)
        return self.yield_str() if self.yield_len() > 0 or self.reaches_end() else self.next_token()

    # ========================================== Text processing ==========================================

    def source_len(self) -> int:
        return len(self.__text)

    def reaches_end(self, offset: int = 0) -> bool:
        return self.__parse_idx + offset >= self.source_len()

    def peek(self, offset: int = 0, count: int = 1) -> str:
        peek_index = self.__parse_idx + offset
        if peek_index < 0 or peek_index >= self.source_len():
            return ''
        return self.__text[peek_index : peek_index + count]

    def offset(self, offset):
        self.__parse_idx += offset
        if self.__parse_idx < 0:
            self.__parse_idx = 0
        elif self.__parse_idx > self.source_len():
            self.__parse_idx = self.source_len()

    def matches(self, text: str) -> bool:
        return self.peek(0, len(text)) == text

    def offset_until(self, text: str) -> bool:
        text_len = len(text)
        while not self.reaches_end(text_len):
            if self.matches(text):
                return True
            self.offset(1)
        self.offset(text_len)
        return False

    def yield_len(self) -> int:
        return self.__parse_idx - self.__mark_idx

    def yield_str(self) -> str:
        slice_str = self.__text[self.__mark_idx: self.__parse_idx]
        self.__mark_idx = self.__parse_idx
        return slice_str

    # ========================================== Sub Check ==========================================

    def __check_meet_token(self) -> str:
        c = self.peek()
        for token in self.__tokens:
            if c == token[0] and self.matches(token):
                self.__wrapper_index = 0
                self.__in_wrapper = False
                for wrapper in self.__wrappers:
                    if token == wrapper[0]:
                        self.__in_wrapper = True
                        break
                    self.__wrapper_index += 1
                return token
        return ''

    def __check_escape_symbol(self) -> bool:
        for symbol in self.__escape_symbols:
            if self.peek(-len(symbol), len(symbol)) == symbol:
                return True
        return False


# ---------------------------------------------------- Token Parser ----------------------------------------------------

LABEL_TAG_TOKENS = [':', ',', ';', '#', '"""', '\n', ' ']
LABEL_TAG_WRAPPERS = [('"""', '"""'), ('#', '\n')]
LABEL_TAG_ESCAPES_SYMBOLS = ['\\']


class LabelTagParser:
    def __init__(self):
        self.__last_tags = []
        self.__label_tags = []

    def get_label_tags(self) -> list:
        return self.__label_tags

    def parse(self, text: str) -> bool:
        parser = TokenParser()
        parser.config(LABEL_TAG_TOKENS, LABEL_TAG_WRAPPERS, LABEL_TAG_ESCAPES_SYMBOLS)
        parser.reset()
        parser.attach(text)

        ret = True
        until = ''
        expect = []
        next_step = 'label'

        while not parser.reaches_end():
            token = parser.next_token()

            print('-> Read token: ' + token)

            if until != '':
                if token == until:
                    until = ''
                continue
            elif len(expect) > 0:
                if token not in expect:
                    ret = False
                    print('! Expect token: ' + str(expect) + ' but met: ' + token)
                expect = []

            if token == '#':
                until = '\n'
            elif token in [':', ',', '"""']:
                print('Drop token: ' + token)

            elif token == '\n' or token == ';':
                next_step = 'label'
            elif next_step == 'label':
                expect = [':', ';']
                next_step = 'tag'
                self.switch_label(token)
            elif next_step == 'tag':
                expect = [',', '\n', '"""', ';']
                self.append_tag(token)
            else:
                print('Should not reach here.')
        return ret

    def switch_label(self, label: str):
        self.__last_tags = []
        self.__label_tags.append((label, self.__last_tags))

    def append_tag(self, tag: str):
        if self.__last_tags is not None and tag not in self.__last_tags:
            self.__last_tags.append(tag)

    @staticmethod
    def label_tags_to_text(label: str, tags, new_line: str = '\n'):
        if label is None or len(label) == 0:
            return ''
        else:
            tag_text = LabelTagParser.tags_to_text(tags, True)
            if len(tag_text) == 0:
                return ''
        return label + ': ' + tag_text + new_line

    @staticmethod
    def tags_to_text(tags, persistence: bool = False):
        if tags is None:
            return ''
        if isinstance(tags, (list, tuple)):
            if persistence:
                tags = [LabelTagParser.check_wrap_tag(tag.strip()) for tag in tags]
            if len(tags) > 0:
                text = ', '.join(tags)
            else:
                return ''
        else:
            text = LabelTagParser.check_wrap_tag(tags)
        return text

    @staticmethod
    def check_wrap_tag(tag: any) -> str:
        if not isinstance(tag, str):
            tag = str(tag)
        tag = tag.replace('"""', '\\"""')
        # tag = tag.replace('\\', '\\\\')
        for token in LABEL_TAG_TOKENS:
            if token in tag:
                return '"""' + tag + '"""'
        return tag

    @staticmethod
    def label_tags_list_to_dict(label_tags_list: [str, [str]]) -> dict:
        label_tags_dict = {}
        for label, tags in label_tags_list:
            if label not in label_tags_list:
                label_tags_dict[label] = []
            label_tags_dict[label].extend(tags)
        return label_tags_dict


# --------------------------------------------------- class LabelTag ---------------------------------------------------

class LabelTag:
    def __init__(self):
        self.__label_tags = {}

    def reset(self):
        self.__label_tags.clear()

    def attach(self, label_tags_list: list):
        self.__label_tags = LabelTagParser.label_tags_list_to_dict(label_tags_list)

        # self.__label_tags.clear()
        # for label, tags in raw_label_tags:
        #     if label not in self.__label_tags:
        #         self.__label_tags[label] = []
        #     self.__label_tags[label].extend(tags)

    def get_tags(self, label: str) -> [str]:
        return self.__label_tags.get(label, [])

    def get_labels(self) -> [str]:
        return list(self.__label_tags.keys())

    def get_label_tags(self) -> dict:
        return self.__label_tags

    def is_label_empty(self, label: str) -> bool:
        tags = self.__label_tags.get(label)
        tags_text = LabelTagParser.tags_to_text(tags)
        return tags_text == ''

    def add_tags(self, label: str, tags: str or [str]):
        if not isinstance(tags, (list, tuple)):
            tags = [tags]
        if label not in self.__label_tags.keys():
            self.__label_tags[label] = tags
        else:
            self.__label_tags[label].extend(tags)
        self.__label_tags[label] = list_unique(self.__label_tags[label])

    def remove_label(self, label: str):
        if label in self.__label_tags.keys():
            del self.__label_tags[label]

    def dump_text(self, labels: [str] = None, compact: bool = False) -> str:
        text = ''
        new_line = '; ' if compact else '\n'
        if labels is None:
            labels = list(self.__label_tags.keys())
        for label in labels:
            tags = self.__label_tags.get(label)
            tags_text = LabelTagParser.tags_to_text(tags, True)
            if tags_text != '':
                text += label + ': ' + tags_text + new_line
        return text

    def filter(self,
               include_label_tags: dict, include_all: bool = True,
               exclude_label_tags: dict = None, exclude_any: bool = True) -> bool:
        if include_label_tags is not None and len(include_label_tags) > 0 and \
                not self.includes(include_label_tags, include_all):
            return False
        if exclude_label_tags is not None and len(exclude_label_tags) > 0 and \
                self.includes(exclude_label_tags, not exclude_any):
            return False
        return True

    def includes(self, label_tag_dict: dict, include_all: bool = False):
        result = False
        for key in label_tag_dict:
            if key not in self.__label_tags.keys():
                if include_all:
                    return False
                else:
                    continue
            expect_tags = label_tag_dict[key]
            exists_tags = self.__label_tags[key]
            for expect_tag in expect_tags:
                if expect_tag not in exists_tags:
                    if include_all:
                        return False
                else:
                    if include_all:
                        result = True
                    else:
                        return True
        return result

    # @staticmethod
    # def tags_to_text(tags: [str]) -> str:
    #     if tags is None:
    #         return ''
    #     elif isinstance(tags, str):
    #         return tags
    #     elif isinstance(tags, (list, tuple)):
    #         return ', '.join(tags)
    #     else:
    #         return str(tags)


# ----------------------------------------------- class HistoricalRecord -----------------------------------------------

class HistoricalRecord(LabelTag):
    # Five key labels of an record: time, location, people, organization, event
    # Optional common labels: title, brief, uuid, author, tags

    def __init__(self, source: str = ''):
        super(HistoricalRecord, self).__init__()
        self.__uuid = str(uuid.uuid4())
        self.__since = 0.0
        self.__until = 0.0
        self.__focus_label = ''
        self.__record_source = source

    # ------------------------------------------------------ Gets ------------------------------------------------------

    def uuid(self) -> str:
        return self.__uuid

    def since(self) -> HistoryTime.TICK:
        return self.__since

    def until(self) -> HistoryTime.TICK:
        return self.__until

    def source(self) -> str:
        return self.__record_source

    def get_focus_label(self) -> str:
        return self.__focus_label

    # -------------------------------------------

    def time(self) -> [str]:
        return self.get_tags('time')

    def people(self) -> list:
        return self.tags('people')

    def location(self) -> list:
        return self.tags('location')

    def organization(self) -> list:
        return self.tags('organization')

    def title(self) -> str:
        return self.get_tags('title')

    def brief(self) -> str:
        return self.get_tags('brief')

    def event(self) -> str:
        return self.get_tags('event')

    def abstract(self) -> str:
        brief = self.get_tags('abstract_brief')
        return brief if brief is not None and len(brief) > 0 else self.abstract_brief()

    # ---------------------------------------------------- Features ----------------------------------------------------

    def reset(self):
        self.__focus_label = ''
        self.__record_source = ''
        super(HistoricalRecord, self).reset()

    def set_source(self, source: str):
        self.__record_source = source

    def set_focus_label(self, label: str):
        self.__focus_label = label

    def set_label_tags(self, label: str, tags: str or [str]):
        if isinstance(tags, str):
            tags = [tags]
        tags = [tag.strip() for tag in tags]

        if label == 'uuid':
            self.__uuid = str(tags[0])
        elif label == 'time':
            self.__try_parse_time_tags(tags)
            # if len(error_list) > 0:
            #     print('Warning: Cannot parse the time tag - ' + str(error_list))
        elif label == 'since':
            self.__since = HistoryTime.decimal_year_to_tick(float(tags[0]))
            return
        elif label == 'until':
            self.__until = HistoryTime.decimal_year_to_tick(float(tags[0]))
            return
        elif label == 'source':
            self.__record_source = str(tags[0])
            return
        super(HistoricalRecord, self).add_tags(label, tags)

    def to_index(self):
        record = HistoricalRecord()
        record.index_for(self)
        return record

    def index_for(self, his_record):
        self.reset()
        self.__focus_label = 'index'
        self.__uuid = his_record.uuid()
        self.__since = his_record.since()
        self.__until = his_record.until()
        self.__record_source = his_record.source()
        self.set_label_tags('abstract', self.abstract_brief())

    def period_adapt(self, since: float, until: float):
        return (self.__since <= until) and (self.__until >= since)

    def abstract_brief(self) -> str:
        abstract = LabelTagParser.tags_to_text(self.get_tags('title'))
        abstract = LabelTagParser.tags_to_text(self.get_tags('brief')) if abstract == '' else abstract
        abstract = LabelTagParser.tags_to_text(self.get_tags('event')) if abstract == '' else abstract
        return abstract.strip()[:50]

    @staticmethod
    def check_label_tags(self, label: str, tags: str or [str]) -> [str]:
        """
        Check label tags error.
        :param label:
        :param tags:
        :return: Error string list. The list is empty if there's no error occurs.
        """
        if label == 'time':
            time_list, error_list = HistoryTime.standardize(','.join(tags))
            return error_list
        else:
            return []

    def dump_record(self, compact: bool = False) -> str:
        new_line = '; ' if compact else '\n'
        dump_list = self.__get_sorted_labels()

        # Default focus label is 'event'
        if self.__focus_label is None or self.__focus_label == '':
            self.__focus_label = 'event'

        # Move the focus label to the tail.
        if self.__focus_label in dump_list:
            dump_list.remove(self.__focus_label)
        dump_list.append(self.__focus_label)

        # uuid should not in the common dump list
        if 'uuid' in dump_list:
            dump_list.remove('uuid')

        # Extra: The start label of HistoricalRecord
        text = LabelTagParser.label_tags_to_text('[START]', self.__focus_label, new_line)

        # Extra: The uuid of event
        if self.__uuid is None or self.__uuid == '':
            self.__uuid = str(uuid.uuid4())
        text += LabelTagParser.label_tags_to_text('uuid', self.__uuid, new_line)

        # ---------------------- Dump common labels ----------------------
        text += super(HistoricalRecord, self).dump_text(dump_list, compact)

        if self.__focus_label == 'index':
            text += LabelTagParser.label_tags_to_text('since', HistoryTime.tick_to_decimal_year(self.since()), new_line)
            text += LabelTagParser.label_tags_to_text('until', HistoryTime.tick_to_decimal_year(self.until()), new_line)
            text += LabelTagParser.label_tags_to_text('source', self.source(), new_line)

        # If the focus label missing, add it with 'end' tag
        if self.__focus_label not in dump_list or self.is_label_empty(self.__focus_label):
            # text += self.__focus_label + ': end' + new_line
            text += LabelTagParser.label_tags_to_text(self.__focus_label, 'end', new_line)

        return text

    #     if not check_condition_range(argv, 'time', self.__time):
    #         return False
    #     if 'contains' in argv.keys():
    #         looking_for = argv['contains']
    #         if self.__title.find(looking_for) == -1 and \
    #            self.__brief.find(looking_for) == -1 and \
    #            self.__event.find(looking_for) == -1:
    #             return False
    #     if not self.__check_label_tags(argv):
    #         return False
    #     return True
    #
    # def __check_label_tags(self, expected: dict) -> bool:
    #     for key in expected:
    #         if key in ['time', 'title', 'brief', 'contains']:
    #             continue
    #         if key not in self.__label_tags.keys():
    #             return False
    #         expected_tags = expected.get(key)
    #         history_event_tags = self.__label_tags.get(key)
    #         if isinstance(expected_tags, (list, tuple)):
    #             return compare_intersection(expected_tags, history_event_tags)
    #         else:
    #             return expected_tags in history_event_tags
    #     return True

    def __try_parse_time_tags(self, tags: [str]):
        his_times = HistoryTime.time_text_to_history_times(','.join(tags))
        if len(his_times) > 0:
            self.__since = min(his_times)
            self.__until = max(his_times)
        else:
            self.__since = 0.0
            self.__until = 0.0

        # time_list, error_list = HistoryTime.standardize(','.join(tags))
        # if len(time_list) > 0:
        #     self.__since = min(time_list)
        #     self.__until = max(time_list)
        # else:
        #     self.__since = 0.0
        #     self.__until = 0.0
        # return error_list

    def __get_sorted_labels(self) -> [str]:
        dump_list = []
        label_list = self.get_labels()

        # Sort the labels and put the focus label at the tail of list

        if 'time' in label_list:
            dump_list.append('time')
            label_list.remove('time')
        if 'people' in label_list:
            dump_list.append('people')
            label_list.remove('people')
        if 'location' in label_list:
            dump_list.append('location')
            label_list.remove('location')
        if 'organization' in label_list:
            dump_list.append('organization')
            label_list.remove('organization')

        dump_list.extend(sorted(label_list))

        if 'title' in dump_list:
            dump_list.remove('title')
            dump_list.append('title')
        if 'brief' in label_list:
            dump_list.remove('brief')
            dump_list.append('brief')
        if 'event' in label_list:
            dump_list.remove('event')
            dump_list.append('event')

        return dump_list

    # ----------------------------------------------------- print ------------------------------------------------------

    def __str__(self):
        return '---------------------------------------------------------------------------' + '\n' + \
                '|UUID   : ' + str(self.__uuid) + '\n' + \
                '|TIME   : ' + str(self.time()) + '\n' + \
                '|TITLE  : ' + str(self.title()) + '\n' + \
                '|BRIEF  : ' + str(self.brief()) + '\n' + \
                '|EVENT  : ' + str(self.event()) + '\n' + \
                '|SOURCE : ' + str(self.__record_source) + '\n' + \
                '---------------------------------------------------------------------------' \
               if self.__focus_label != 'index' else \
               '---------------------------------------------------------------------------' + '\n' + \
                '|UUID     : ' + str(self.uuid()) + '\n' + \
                '|SINCE    : ' + str(self.since()) + '\n' + \
                '|UNTIL    : ' + str(self.until()) + '\n' + \
                '|ABSTRACT : ' + str(self.get_tags('abstract')) + '\n' + \
                '|SOURCE   : ' + str(self.__record_source) + '\n' + \
                '---------------------------------------------------------------------------'


# --------------------------------------------------- class history ----------------------------------------------------

class HistoricalRecordLoader:
    def __init__(self):
        self.__records = []

    def restore(self):
        self.__records.clear()

    def get_loaded_records(self) -> list:
        return self.__records

    @staticmethod
    def to_local_depot(records: HistoricalRecord or [HistoricalRecord], depot: str, source: str) -> bool:
        base_name = os.path.basename(source)
        depot_path = HistoricalRecordLoader.join_local_depot_path(depot)
        source = path.join(depot_path, base_name)
        HistoricalRecordLoader.to_local_source(records, source)

    @staticmethod
    def to_local_source(records: HistoricalRecord or [HistoricalRecord], source: str):
        if not isinstance(records, (list, tuple)):
            records = [records]
        try:
            full_path = HistoricalRecordLoader.source_to_absolute_path(source)
            print('| <= Write record: ' + full_path)
            with open(full_path, 'wt', encoding='utf-8') as f:
                for record in records:
                    text = record.dump_record()
                    f.write(text)
            return True
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return False
        finally:
            pass

    def from_local_depot(self, depot: str) -> int:
        try:
            depot_path = HistoricalRecordLoader.join_local_depot_path(depot)
            return self.from_directory(depot_path)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return 0
        finally:
            pass

    def from_directory(self, directory: str) -> int:
        try:
            files = HistoricalRecordLoader.enumerate_local_path(directory)
            return self.from_files(files)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return 0
        finally:
            pass

    def from_source(self, source: str) -> bool:
        if HistoricalRecordLoader.is_web_url(source):
            return self.from_web()
        else:
            return self.from_file(HistoricalRecordLoader.source_to_absolute_path(source))

    def from_files(self, files: [str]) -> int:
        count = 0
        for file in files:
            if self.from_file(file):
                count += 1
        return count

    def from_web(self, url: str) -> bool:
        try:
            r = requests.get(url)
            text = r.content.decode('utf-8')
            self.from_text(text)
            return True
        except Exception as e:
            print('Error when fetching from web: ' + str(e))
            return False
        finally:
            pass

    def from_file(self, file: str) -> bool:
        try:
            print('| => Load record: ' + file)
            with open(file, 'rt', encoding='utf-8') as f:
                self.from_text(f.read(), file)
            return True
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return False
        finally:
            pass

    def from_text(self, text: str, source: str = ''):
        error_list = []

        parser = LabelTagParser()
        parser.parse(text)

        focus = ''
        record = None
        label_tags = parser.get_label_tags()

        for label, tags in label_tags:
            if label == '[START]':
                self.yield_record(record)
                record = None
                focus = ''
                if len(tags) == 0:
                    error_list.append('Missing start section.')
                else:
                    focus = tags[0]
                continue

            if record is None:
                record = HistoricalRecord(HistoricalRecordLoader.normalize_source(source))
                record.set_focus_label(focus)
            record.set_label_tags(label, tags)

            if focus != '' and label == focus:
                self.yield_record(record)
                record = None
                focus = ''
        self.yield_record(record)

    def yield_record(self, record):
        if record is not None:
            self.__records.append(record)

    @staticmethod
    def is_web_url(_path: str):
        return _path.startswith('http') or _path.startswith('ftp')

    @staticmethod
    def is_absolute_path(_path: str):
        return ntpath.isabs(_path) or posixpath.isabs(_path)

    @staticmethod
    def source_to_absolute_path(source: str) -> str:
        return source if \
            HistoricalRecordLoader.is_absolute_path(source) else \
            path.join(HistoricalRecordLoader.get_local_depot_root(), source)

    @staticmethod
    def normalize_source(source: str) -> str:
        depot_root = HistoricalRecordLoader.get_local_depot_root()
        return source[len(depot_root) + 1:] if source.startswith(depot_root) else source

    @staticmethod
    def get_local_depot_root() -> str:
        project_root = path.dirname(path.abspath(__file__))
        depot_path = path.join(project_root, 'depot')
        return depot_path

    @staticmethod
    def join_local_depot_path(depot: str) -> str:
        root_path = HistoricalRecordLoader.get_local_depot_root()
        depot_path = path.join(root_path, depot)
        return depot_path

    @staticmethod
    def enumerate_local_path(root_path: str, suffix: [str] = None) -> list:
        files = []
        for parent, dirnames, filenames in os.walk(root_path):
            for filename in filenames:
                if suffix is None:
                    files.append(path.join(parent, filename))
                else:
                    for sfx in suffix:
                        if filename.endswith(sfx):
                            files.append(path.join(parent, filename))
                            break
        return files


# ------------------------------------------- class HistoricalRecordIndexer --------------------------------------------

class HistoricalRecordIndexer:
    def __init__(self):
        self.__indexes = []

    def restore(self):
        self.__indexes = []

    def get_indexes(self) -> list:
        return self.__indexes

    def index_path(self, directory: str):
        loader = HistoricalRecordLoader()
        his_filels = HistoricalRecordLoader.enumerate_local_path(directory)
        for his_file in his_filels:
            loader.from_file(his_file)
            records = loader.get_loaded_records()
            self.index_records(records)
            loader.restore()

    def index_records(self, records: list):
        for record in records:
            index = HistoricalRecord()
            index.index_for(record)
            self.__indexes.append(index)

    def replace_index_prefix(self, prefix_old: str, prefix_new: str):
        for index in self.__indexes:
            if index.source.startswith(prefix_old):
                index.source.replace(prefix_old, prefix_new)

    def dump_to_file(self, file: str):
        print('| => Write record: ' + file)
        with open(file, 'wt', encoding='utf-8') as f:
            for index in self.__indexes:
                text = index.dump_record(True)
                f.write(text + '\n')

    def load_from_file(self, file: str):
        loader = HistoricalRecordLoader()
        loader.from_file(file)
        self.__indexes = loader.get_loaded_records()

    def print_indexes(self):
        for index in self.__indexes:
            print(index)


# --------------------------------------------------- class history ----------------------------------------------------

class History:
    def __init__(self):
        self.__records = []
        # Deprecated
        self.__indexes = []

    # ----------------------------------- Deprecated :Index -----------------------------------

    def set_indexes(self, indexes: [HistoricalRecord]):
        self.__indexes.clear()
        self.__indexes.extend(indexes)

    def get_indexes(self) ->[HistoricalRecord]:
        return self.__indexes

    # -------------------------------------- Gets / Sets --------------------------------------

    def add_record(self, record: HistoricalRecord) -> bool:
        if record is None or record.uuid() is None or record.uuid() == '':
            return False
        _uuid = record.uuid()
        exists_record = self.get_record_by_uuid(_uuid)
        if exists_record is not None:
            self.__records.remove(exists_record)
        self.__records.append(record)
        return True

    def remove_record(self, record: HistoricalRecord):
        if record in self.__records:
            self.__records.remove(record)

    def add_records(self, records: [HistoricalRecord]):
        for record in records:
            self.add_record(record)

    def remove_records(self, records: [HistoricalRecord]):
        for record in records:
            self.remove_record(record)

    def get_records(self) -> [HistoricalRecord]:
        return self.__records

    def attach_records(self, records: [HistoricalRecord]):
        self.__records.clear()
        self.__records.extend(records)

    def clear_records(self):
        self.__records.clear()

    # --------------------------------------- Updates ---------------------------------------

    def update_records(self, records: [HistoricalRecord]):
        History.upsert_records(self.__records, records)

    def update_indexes(self, indexes: [HistoricalRecord]):
        History.upsert_records(self.__indexes, indexes)

    # --------------------------------------- Select ---------------------------------------

    def get_record_by_uuid(self, _uuid: str) -> HistoricalRecord or None:
        for record in self.__records:
            if record.uuid() == _uuid:
                return record
        return None

    def get_record_by_source(self, source: str) -> HistoricalRecord or None:
        return [record for record in self.__records if record.source() == source]

    def select_records(self, _uuid: str or [str] = None,
                       sources: str or [str] = None, focus_label: str = '',
                       include_label_tags: dict = None, include_all: bool = True,
                       exclude_label_tags: dict = None, exclude_any: bool = True) ->[HistoricalRecord]:
        records = self.__records.copy()

        if _uuid is not None and len(_uuid) != 0:
            if not isinstance(_uuid, (list, tuple)):
                _uuid = [_uuid]
            records = [record for record in records if record.uuid() in _uuid]

        if sources is not None and len(sources) != 0:
            if not isinstance(sources, (list, tuple)):
                sources = [sources]
            records = [record for record in records if record.source() in sources]

        if focus_label is not None and focus_label != '':
            records = [record for record in records if record.get_focus_label() == focus_label]

        if include_label_tags is not None or exclude_label_tags is not None:
            records = [record for record in records if record.filter(include_label_tags, include_all,
                                                                     exclude_label_tags, exclude_any)]
        return records

    # ------------------------------------- Load -------------------------------------

    def load_source(self, source: str) -> [HistoricalRecord]:
        loader = HistoricalRecordLoader()
        result = loader.from_source(source)
        if result:
            self.add_records(loader.get_loaded_records())
        return loader.get_loaded_records() if result else []

    def load_depot(self, depot: str) -> bool:
        loader = HistoricalRecordLoader()
        result = loader.from_local_depot(depot)
        if result:
            self.add_records(loader.get_loaded_records())
        return result != 0

    def load_path(self, _path: str):
        loader = HistoricalRecordLoader()
        result = loader.from_directory(_path)
        if result:
            self.add_records(loader.get_loaded_records())
        return result != 0

    # ----------------------------------- Print -----------------------------------

    def print_records(self):
        for record in self.__records:
            print(record)

    def print_indexes(self):
        for index in self.__indexes:
            print(index)

    # ------------------------------- Static Methods -------------------------------

    @staticmethod
    def sort_records(records: [HistoricalRecord]) -> [HistoricalRecord]:
        return sorted(records, key=lambda x: x.since())

    @staticmethod
    def unique_records(records: [HistoricalRecord]) -> [HistoricalRecord]:
        return {r.uuid(): r for r in records}.values()

    @staticmethod
    def upsert_records(records_list: [HistoricalRecord], records_new: [HistoricalRecord]):
        new_records = {r.uuid(): r for r in records_new}
        for i in range(0, len(records_list)):
            _uuid = records_list[i].uuid()
            if _uuid in new_records.keys():
                records_list[i] = new_records[_uuid]
                del new_records[_uuid]
        records_list.extend(new_records.values())


# ----------------------------------------------------- Test Code ------------------------------------------------------

# ---------------------------- Token & Parser ----------------------------

def test_token_parser(text: str, expects: [str], tokens: list, wrappers: list, escape_symbols: list):
    parser = TokenParser()
    parser.config(tokens, wrappers, escape_symbols)
    parser.reset()
    parser.attach(text)
    for expect in expects:
        token = parser.next_token()
        assert token == expect


def test_token_parser_case_normal():
    text = '''
    line1:abc            # text in: comments
    line2
    line3:"""text in :wrapper"""
    '''
    expects = [
        '\n',
        'line1',
        ':',
        'abc',
        '#',
        ' text in: comments',
        '\n',
        'line2',
        '\n',
        'line3',
        ':',
        '"""',
        'text in :wrapper',
        '"""',
        '\n',
        ''
    ]
    test_token_parser(text, expects, LABEL_TAG_TOKENS, LABEL_TAG_WRAPPERS, LABEL_TAG_ESCAPES_SYMBOLS)


def test_token_parser_case_escape_symbol():
    pass


# -------------------------------- History --------------------------------

def test_history_basic():
    loader = HistoricalRecordLoader()
    count = loader.from_local_depot('example')

    print('Load successful: ' + str(count))

    history = History()
    records = loader.get_loaded_records()
    history.update_records(records)
    history.print_records()


def test_history_filter():
    loader = HistoricalRecordLoader()
    loader.from_local_depot('example')

    history = History()
    history.update_records(loader.get_loaded_records())

    records = history.select_records(include_label_tags={'tags': ['tag1']},
                                     include_all=True)
    assert len(records) == 1

    records = history.select_records(include_label_tags={'tags': ['tag3']},
                                     include_all=True)
    assert len(records) == 3

    records = history.select_records(include_label_tags={'tags': ['tag5', 'odd']},
                                     include_all=True)
    assert len(records) == 3

    records = history.select_records(include_label_tags={'tags': ['tag1', 'even']},
                                     include_all=False)
    assert len(records) == 3

    records = history.select_records(include_label_tags={'tags': ['tag']},
                                     include_all=True)
    assert len(records) == 0

    records = history.select_records(include_label_tags={'author': ['Sleepy']},
                                     include_all=True)
    assert len(records) == 4


# -------------------------------- Indexer --------------------------------

def test_generate_index():
    depot_path = HistoricalRecordLoader.join_local_depot_path('China')
    indexer = HistoricalRecordIndexer()
    indexer.index_path(depot_path)
    indexer.dump_to_file('test_history.index')


def test_load_index():
    indexer = HistoricalRecordIndexer()
    indexer.load_from_file('test_history.index')
    history = History()
    history.update_indexes(indexer.get_indexes())
    history.print_indexes()


# ----------------------------------------------------- File Entry -----------------------------------------------------

def main():
    test_history_time_year()
    test_history_time_year_month()
    test_time_text_to_history_times()
    test_token_parser_case_normal()
    test_token_parser_case_escape_symbol()
    test_history_basic()
    test_history_filter()
    test_generate_index()
    test_load_index()
    print('All test passed.')


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










