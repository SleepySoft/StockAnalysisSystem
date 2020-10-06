from flask import request
from StockAnalysisSystem.core.config import Config

from . import analyzer_service


SIMPLE_TEMPLATE = '''
<html>
<header>%s分析结果</header>
<body>
%s
</body>
</html>
'''


def init(config: Config):
    analyzer_service.init(config)


def analysis(flask_request: request) -> str:
    args = flask_request.args
    security = args.get('security', '')
    if security == '':
        html = SIMPLE_TEMPLATE % (security, '找不到股票分析信息')
    else:
        html = SIMPLE_TEMPLATE % (security, analyzer_service.analysis(security))
    return html









