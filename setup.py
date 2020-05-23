import os
import shutil
from setuptools import setup, find_packages

root_path = os.path.dirname(__file__)


def pack_files(directory) -> [str]:
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        if '__pycache__' in path:
            continue
        for filename in filenames:
            paths.append(os.path.join('.', path, filename))
    return paths


def pack_plugin() -> list:
    shutil.rmtree(os.path.join(root_path, 'plugin', 'Analyzer', '__pycache__'), ignore_errors=True)
    shutil.rmtree(os.path.join(root_path, 'plugin', 'Collector', '__pycache__'), ignore_errors=True)
    shutil.rmtree(os.path.join(root_path, 'plugin', 'Extension', '__pycache__'), ignore_errors=True)
    shutil.rmtree(os.path.join(root_path, 'plugin', 'Factor', '__pycache__'), ignore_errors=True)
    return pack_files('plugin')

    # return {
    #     'plugin/Analyzer', pack_files('plugin/')
    #     'plugin/Collector', pack_files('plugin')
    #     'plugin/Extension', pack_files('plugin')
    #     'plugin/Factor', pack_files('plugin')
    # }


def pack_params(**kwargs) -> dict:
    return kwargs


if __name__ == "__main__":
    # extra_files = pack_plugin()

    setup_params = pack_params(
        name='StockAnalysisSystem',
        version='0.0.7',
        license='Apache License',

        keywords='stock analysis system sas',
        description='Stock Analysis System',
        long_description='A framework for stock analysis',

        author='Sleepy',
        author_email='sleepysoft@gmail.com',

        maintainer='Sleepy',
        maintainer_email='sleepysoft@gmail.com',

        url='https://gitee.com/SleepySoft/StockAnalysisSystem',

        packages=find_packages(exclude=["Test", 'test', "*.tests", "*.tests.*"]),

        # packages=find_packages(where='StockAnalysisSystem', exclude=["Test", 'test', "*.tests", "*.tests.*"]),
        # package_dir={'': 'StockAnalysisSystem'},

        platforms='any',
        install_requires=[
            'pyqt5',
            'pyqtwebengine',
            'bs4',
            'lxml',
            'requests',
            'pandas',
            'pymongo',
            'openpyxl',
            'tushare',
            'pylab-sdk',
            'matplotlib',
            'requests_html',
            'PyExecJS',
        ],

        # data_files=[
        #     ('StockAnalysisSystem/plugin', extra_files),
        # ],
    )
    setup(**setup_params)
