import os
import glob
from setuptools import setup, find_packages


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        if '__pycache__' in path:
            continue
        for filename in filenames:
            paths.append(os.path.join('.', path, filename))
    return paths


def pack_params(**kwargs) -> dict:
    return kwargs


if __name__ == "__main__":
    # root_path = os.path.abspath(os.path.dirname(__file__))
    # plugin_path = os.path.join(root_path, 'plugin', '**', '*')
    # plugin_files = [filename for filename in glob.iglob(plugin_path, recursive=True)]

    extra_files = package_files('plugin')

    setup_params = pack_params(
        name='StockAnalysisSystem',
        version='0.0.6',
        license='Apache License',

        keywords='stock analysis system sas',
        description='Stock Analysis System',
        long_description='A framework for stock analysis',

        author='Sleepy',
        author_email='sleepysoft@gmail.com',

        maintainer='Sleepy',
        maintainer_email='sleepysoft@gmail.com',

        url='https://gitee.com/SleepySoft/StockAnalysisSystem',

        packages=find_packages(exclude=["Test", "*.tests", "*.tests.*"]),
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

        data_files=[
            ('plugin', extra_files),
        ],
    )
    setup(**setup_params)
