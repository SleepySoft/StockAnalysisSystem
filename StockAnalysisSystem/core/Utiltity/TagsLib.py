import os
import sys
import json
import traceback


root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class Tags:
    def __init__(self, record_path: str):
        self.__tags_path = record_path
        self.__tag_obj_dict = {}
        self.__obj_tag_dict = {}

    def all_tags(self) -> [str]:
        return list(self.__tag_obj_dict.keys())

    def all_objs(self) -> [str]:
        return list(self.__obj_tag_dict.keys())

    def tags_of_objs(self, objs: str or [str]) -> [str]:
        tags = []
        if not isinstance(objs, (list, tuple)):
            objs = [objs]
        for obj in objs:
            tags.extend(self.__obj_tag_dict.get(obj, []))
        return list(set(tags))

    def objs_from_tags(self, tags: str or [str]) -> [str]:
        objs = []
        if not isinstance(tags, (list, tuple)):
            tags = [tags]
        for tag in tags:
            objs.extend(self.__tag_obj_dict.get(tag, []))
        return list(set(objs))

    def set_obj_tags(self, obj: str, tags: str or [str]):
        if not isinstance(tags, (list, tuple)):
            tags = [tags]
        self.clear_obj_tags(obj)
        self.__obj_tag_dict[obj] = tags
        for tag in tags:
            if tag not in self.__tag_obj_dict:
                self.__tag_obj_dict[tag] = [obj]
            elif obj not in self.__tag_obj_dict[tag]:
                self.__tag_obj_dict[tag].append(obj)

    def clear_obj_tags(self, obj: str):
        if obj in self.__obj_tag_dict.keys():
            tags = self.__obj_tag_dict.get(obj, [])
            del self.__obj_tag_dict[obj]
            self.__remove_obj_from_tag_obj_dict(obj, tags)

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
        pass

    @staticmethod
    def str_to_tags(text: str) -> [str]:
        pass


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


def test_entry():
    test_basic()


# ----------------------------------------------------------------------------------------------------------------------

def main():
    test_entry()


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







