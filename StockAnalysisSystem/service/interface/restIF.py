from flask import request
from ..provider.provider import ServiceProvider
from StockAnalysisSystem.core.config import Config


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






