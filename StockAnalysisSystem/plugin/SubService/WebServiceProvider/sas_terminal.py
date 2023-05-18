import StockAnalysisSystem.core.api as sasApi
from StockAnalysisSystem.interface.interface import SasInterface
from StockAnalysisSystem.core.Utility.digit_utility import to_int


class TerminalContext:
    def __init__(self, result_handler, **kwargs):
        self.context = kwargs
        self.result_handler = result_handler


TEXT_SPLITTER = '\n---------------------------------\n'
TEXT_HELP = '''股票名或股票代码：查看股票分析
项目地址：查看此项目开源地址'''


class SasTerminal:
    MIN_INPUT = 3

    def __init__(self, sas_if: SasInterface, sas_api: sasApi):
        self.__sas_if = sas_if
        self.__sas_api = sas_api
        self.__result_url = sas_api.config().get('analysis_result_url', 'http://sleepysoft.xyz/analysis?security=%s')

    def interact(self, ctx: TerminalContext, input_text: str) -> str:
        command, parameter = self.analysis_input_text(input_text)
        result = self.dispatch_command(ctx, command, parameter)
        return result

    # ----------------------------------------------------------------------------------------

    def analysis_input_text(self, input_text: str) -> (str, list or str):
        if input_text.strip() in ['help', '帮助']:
            return 'help', ''

        if len(input_text) < SasTerminal.MIN_INPUT:
            return 'help_brief', ''

        securities = self.__sas_api.data_utility().guess_securities(input_text)
        if len(securities) > 0:
            return 'analysis', securities

        if input_text.strip() == '项目地址':
            return 'project_url', ''

        return 'help_brief', ''

    def dispatch_command(self, ctx: TerminalContext, command: str, parameter: list or str) -> str:
        if command == 'help':
            result = self.command_help()
        elif command == 'help_brief':
            result = self.help_brief()

        elif command == 'project_url':
            result = self.command_url()
        elif command == 'analysis':
            result = self.command_analysis(parameter)

        else:
            result = ''
        return result

    # ----------------------------------------------------------------------------------------
    
    def help_brief(self) -> str:
        return '直接输入股票名或股票代码查看股票分析。\n或输入"帮助"查看详细帮助信息。'

    def command_help(self) -> str:
        return TEXT_HELP
    
    def command_url(self) -> str:
        return 'https://gitee.com/SleepySoft/StockAnalysisSystem'

    def command_analysis(self, securities: str) -> str:
        if len(securities) > 1:
            return '你输入的股票有多种可能\n' + '\n'.join(securities)
        elif len(securities) == 1:
            pass
        else:
            return '你输入的股票不存在'
        stock_identity = securities[0]

        df = self.__sas_api.data_center().query('Result.Analyzer', stock_identity)
        if df is None or df.empty:
            return '无数据'
        df = df.sort_values(by="period").drop_duplicates(subset=["analyzer"], keep="last")

        stock_name = self.__sas_api.data_utility().stock_identity_to_name(stock_identity)
        text = '%s [%s]' % (stock_name, stock_identity)

        if df.empty:
            return text + '无数据'

        strategy_name_dict = self.__sas_api.strategy_entry().strategy_name_dict()

        text_items = []
        for analyzer, period, brief, score in \
                zip(df['analyzer'], df['period'], df['brief'], df['score']):
            if score is not None and to_int(score, 999) <= 60:
                text_items.append('> %s: %s' % (strategy_name_dict.get(analyzer), brief))

        if len(text_items) == 0:
            text += '未发现风险项目'
        else:
            text += '风险项目'
            text += TEXT_SPLITTER
            text += '\n'.join(text_items)

        # url = 'http://211.149.229.160/analysis?security=%s' % stock_identity
        url = self.__result_url % stock_identity
        result_link = '详情: %s' % url
        text += TEXT_SPLITTER
        text += result_link

        return text

        # # Warning: Advanced operation - Directly operate database collection
        #
        # from StockAnalysisSystem.core.DataHub.DataAgent import DataAgent
        # from StockAnalysisSystem.core.UniversalDataDepot.DepotMongoDB import DepotMongoDB
        #
        # agent: DataAgent = self.__sas_api.data_center().get_data_agent('Result.Analyzer')
        # if agent is None:
        #     return '数据不支持'
        #
        # prob = agent.prob()
        # depot: DepotMongoDB = prob.get('depot', None)
        # if not isinstance(depot, DepotMongoDB):
        #     return '数据不支持'
        #
        # collection = depot.raw()
        # if collection is None:
        #     return '数据不支持'
        #
        # result = collection.aggregate([
        #     {'$match': {'stock_identity': securities[0]}},
        #     {'$sort': {'period': -1, 'analyzer': -1}},
        #     {'$group': {
        #         '_id': None,
        #         'period': {'$last': '$period'},
        #         'analyzer': {'$first': '$analyzer'}
        #     }}
        # ])
        # result_l = list(result)
