import os
from flask import request
from StockAnalysisSystem.core.config import Config
from StockAnalysisSystem.core.Utility.relative_import import RelativeImport

with RelativeImport(__file__):
    from service_provider import ServiceProvider


service_provider: ServiceProvider = None


def analysis(flask_request: request) -> str:
    args = flask_request.args
    security = args.get('security', '')
    return service_provider.get_security_analysis_result_page(security)


# def query(flask_request: request):
#     args = flask_request.args
#     uri = args.get('uri', None)
#     identity = args.get('security', None)
#     since = args.get('since', None)
#     until = args.get('since', None)
#     return service_provider.query(uri=uri, identity=identity, since=since, until=until)


# ----------------------------------------------------------------------------------------------------------------------

def init(provider: ServiceProvider, config: Config):
    global service_provider
    service_provider = provider






