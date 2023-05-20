import sys
import logging


class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != '\n':
            self.logger.log(self.level, message)

    def flush(self):
        pass


def logging_config():
    # 配置日志记录器
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler('sas_service.log', mode='wt'),
            logging.StreamHandler()
        ]
    )

    # 获取根记录器并设置日志级别
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 创建一个 LoggerWriter 对象并将其设置为 sys.stdout
    sys.stdout = LoggerWriter(root_logger, logging.INFO)


def logging_test():
    logging.debug('Debug log')
    logging.info('Info log')
    logging.warning('Warning log')
    logging.error('Error log')
    logging.critical('Critical log')
    print('Log from print')
