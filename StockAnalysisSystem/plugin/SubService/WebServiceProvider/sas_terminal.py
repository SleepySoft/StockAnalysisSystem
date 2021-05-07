import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.interface.interface import SasInterface


class TerminalContext:
    def __init__(self, result_handler, **kwargs):
        self.context = kwargs
        self.result_handler = result_handler


class SasTerminal:
    MIN_INPUT = 3

    def __init__(self, sas_if: SasInterface, sas_api: sasApi):
        self.__sas_if = sas_if
        self.__sas_api = sas_api
        self.__offline_analysis_result = None

    def interact(self, ctx: TerminalContext, input_text: str) -> str:
        command, parameter = self.analysis_input_text(input_text)
        result = self.dispatch_command(ctx, command, parameter)
        return result

    # ----------------------------------------------------------------------------------------

    def analysis_input_text(self, input_text: str) -> (str, list or str):
        if len(input_text) < SasTerminal.MIN_INPUT:
            return 'help', ''

        securities = self.__sas_api.data_utility().guess_securities(input_text)
        if len(securities) > 0:
            return 'analysis', securities

        return 'help', ''

    def dispatch_command(self, ctx: TerminalContext, command: str, parameter: list or str) -> str:
        if command == 'help':
            result = self.command_help()
        elif command == 'analysis':
            result = self.command_analysis(parameter)
        else:
            result = ''
        return result

    # ----------------------------------------------------------------------------------------

    def command_help(self) -> str:
        return '''直接输入股票名或股票代码：查看股票分析
        '''

    def command_analysis(self, securities: str) -> str:
        if len(securities) > 1:
            return '你输入的股票有多种可能\n' + '\n'.join(securities)
        elif len(securities) == 1:
            pass
        else:
            return '你输入的股票不存在'
