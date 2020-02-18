import time
from sys import executable as py_executable
from PyInstaller.__main__ import run as _build_exe
import os as _os
import platform

_here = _os.path.abspath(_os.path.dirname(__file__))
_os.chdir(_here)
_py_executable_path = _os.path.abspath(_os.path.dirname(py_executable))

if platform.system() == 'Windows':
    _build_exe_args = (
        '--clean',
        '--i', 'res/logo.ico',
        '--paths', "./",
        '-n', 'application',
        '-y',
        "main.py"
    )
else:
    _build_exe_args = (
        '--clean',
        '--i', 'res/logo.ico',
        '--paths', "./",
        '-n', 'application',
        '-y',
        "main.py"
    )


def build_exe():
    _build_exe(pyi_args=_build_exe_args)
    pass


def add_data_file():
    src_path = 'Data/'
    dist_path = 'dist/application/Data/'
    from shutil import copytree, rmtree
    if _os.path.exists(dist_path):
        rmtree(dist_path)
    copytree(src_path, dist_path)
    pass


def __only_py(src, names):
    ret = []
    for sub_name in names:
        if not sub_name.endswith('.py'):
            ret.append(sub_name)
            pass
    return ret
    pass


def __add_dir_in_zip(_zip_f, dir_name, arc_pre_path=''):
    file_list = []
    if arc_pre_path and not arc_pre_path.endswith('/'):
        arc_pre_path = '{}/'.format(arc_pre_path)
    if _os.path.isfile(dir_name):
        file_list.append(dir_name)
    else:
        for root, dirs, files in _os.walk(dir_name):
            for name in files:
                file_list.append(_os.path.join(root, name))
    for file in file_list:
        arc_name = file[len(dir_name):]
        print(arc_name)
        _zip_f.write(file, arc_pre_path + arc_name)
    pass


def packing_app(app_pkg_name):
    print('Packing application...')
    if _os.path.exists(app_pkg_name):
        _os.remove(app_pkg_name)
        print(app_pkg_name, 'is removed')
    from zipfile import ZipFile
    with ZipFile(app_pkg_name, 'w') as zip_f:
        __add_dir_in_zip(zip_f, 'dist/application', 'StockAnalysisSystem.Sleepy')
    pass


def format_app_package_name():
    from readme import VERSION as _app_version
    name_format = 'StockAnalysisSystem-{version}-{os_name}_{os_machine}_{date}.zip'
    _os_name = platform.system() + platform.release()
    _os_machine = platform.machine()
    return name_format.format(os_name=_os_name,
                              os_machine=_os_machine,
                              version=_app_version,
                              date=time.strftime("%Y%m%d", time.localtime(time.time()))).lower()
    pass


if __name__ == "__main__":
    try:
        build_exe()
        add_data_file()
        packing_app('dist/{}'.format(format_app_package_name()))
    except Exception as exception:
        print('ERROR:', 'Build failed!', exception)
        import traceback
        traceback.print_exc()
        input()
        pass
    pass
