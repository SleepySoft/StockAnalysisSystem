from flask import request
from ..render.common_render import *
from ..provider.provider import ServiceProvider
from StockAnalysisSystem.core.config import Config


service_provider: ServiceProvider = None


def analysis(flask_request: request) -> str:
    args = flask_request.args
    security = args.get('security', '')
    return service_provider.get_security_analysis_result_page(security)


# ----------------------------------------------------------------------------------------------------------------------

def init(provider: ServiceProvider, config: Config):
    global service_provider
    service_provider = provider






