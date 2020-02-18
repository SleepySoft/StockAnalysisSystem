import os as _os
import shutil

_here = _os.path.abspath(_os.path.dirname(__file__))
_os.chdir(_here)

_remove_paths = (
    'build',
    'dist',
    '__pycache__',
    'application.spec'
)

if __name__ == '__main__':
    for path in _remove_paths:
        if _os.path.exists(path):
            if _os.path.isfile(path):
                _os.remove(path)
                print('[Deleted]', path)
            else:
                shutil.rmtree(path)
                print('[Deleted]', path)
        else:
            print('[Invalid]', path)
    pass
