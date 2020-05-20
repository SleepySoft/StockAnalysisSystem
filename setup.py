from setuptools import setup, find_packages


def pack_params(**kwargs) -> dict:
    return kwargs


if __name__ == "__main__":
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

        packages=find_packages(where='.'),
        include_package_data=True,
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
    )
    setup(**setup_params)
