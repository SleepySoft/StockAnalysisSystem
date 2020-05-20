import pandas as pd
import tushare as ts

from StockAnalysisSystem.core.config import TS_TOKEN
from StockAnalysisSystem.core.Utiltity.common import *
from StockAnalysisSystem.core.Utiltity.time_utility import *
from StockAnalysisSystem.core.Utiltity.CollectorUtility import *


# ----------------------------------------------------------------------------------------------------------------------

FIELDS = {
    'Finance.Audit': {
        'ts_code':                       'TS股票代码',
        'ann_date':                      '公告日期',
        'end_date':                      '报告期',
        'audit_result':                  '审计结果',
        'audit_fees':                    '审计总费用',                          # （元）
        'audit_agency':                  '会计事务所',
        'audit_sign':                    '签字会计师',
    },

    'Finance.BalanceSheet': {
        'ts_code':                       'TS股票代码',
        'ann_date':                      '公告日期',
        'f_ann_date':                    '实际公告日期',
        'end_date':                      '报告期',
        'report_type':                   '报表类型',
        'comp_type':                     '公司类型',
        'total_share':                   '期末总股本',
        'cap_rese':                      '资本公积金',
        'undistr_porfit':                '未分配利润',
        'surplus_rese':                  '盈余公积金',
        'special_rese':                  '专项储备',
        'money_cap':                     '货币资金',
        'trad_asset':                    '交易性金融资产',
        'notes_receiv':                  '应收票据',
        'accounts_receiv':               '应收账款',
        'oth_receiv':                    '其他应收款',
        'prepayment':                    '预付款项',
        'div_receiv':                    '应收股利',
        'int_receiv':                    '应收利息',
        'inventories':                   '存货',
        'amor_exp':                      '长期待摊费用',
        'nca_within_1y':                 '一年内到期的非流动资产',
        'sett_rsrv':                     '结算备付金',
        'loanto_oth_bank_fi':            '拆出资金',
        'premium_receiv':                '应收保费',
        'reinsur_receiv':                '应收分保账款',
        'reinsur_res_receiv':            '应收分保合同准备金',
        'pur_resale_fa':                 '买入返售金融资产',
        'oth_cur_assets':                '其他流动资产',
        'total_cur_assets':              '流动资产合计',
        'fa_avail_for_sale':             '可供出售金融资产',
        'htm_invest':                    '持有至到期投资',
        'lt_eqt_invest':                 '长期股权投资',
        'invest_real_estate':            '投资性房地产',
        'time_deposits':                 '定期存款',
        'oth_assets':                    '其他资产',
        'lt_rec':                        '长期应收款',
        'fix_assets':                    '固定资产',
        'cip':                           '在建工程',
        'const_materials':               '工程物资',
        'fixed_assets_disp':             '固定资产清理',
        'produc_bio_assets':             '生产性生物资产',
        'oil_and_gas_assets':            '油气资产',
        'intan_assets':                  '无形资产',
        'r_and_d':                       '研发支出',
        'goodwill':                      '商誉',
        'lt_amor_exp':                   '长期待摊费用',
        'defer_tax_assets':              '递延所得税资产',
        'decr_in_disbur':                '发放贷款及垫款',
        'oth_nca':                       '其他非流动资产',
        'total_nca':                     '非流动资产合计',
        'cash_reser_cb':                 '现金及存放中央银行款项',
        'depos_in_oth_bfi':              '存放同业和其它金融机构款项',
        'prec_metals':                   '贵金属',
        'deriv_assets':                  '衍生金融资产',
        'rr_reins_une_prem':             '应收分保未到期责任准备金',
        'rr_reins_outstd_cla':           '应收分保未决赔款准备金',
        'rr_reins_lins_liab':            '应收分保寿险责任准备金',
        'rr_reins_lthins_liab':          '应收分保长期健康险责任准备金',
        'refund_depos':                  '存出保证金',
        'ph_pledge_loans':               '保户质押贷款',
        'refund_cap_depos':              '存出资本保证金',
        'indep_acct_assets':             '独立账户资产',
        'client_depos':                  '其中：客户资金存款',
        'client_prov':                   '其中：客户备付金',
        'transac_seat_fee':              '其中:交易席位费',
        'invest_as_receiv':              '应收款项类投资',
        'total_assets':                  '资产总计',
        'lt_borr':                       '长期借款',
        'st_borr':                       '短期借款',
        'cb_borr':                       '向中央银行借款',
        'depos_ib_deposits':             '吸收存款及同业存放',
        'loan_oth_bank':                 '拆入资金',
        'trading_fl':                    '交易性金融负债',
        'notes_payable':                 '应付票据',
        'acct_payable':                  '应付账款',
        'adv_receipts':                  '预收款项',
        'sold_for_repur_fa':             '卖出回购金融资产款',
        'comm_payable':                  '应付手续费及佣金',
        'payroll_payable':               '应付职工薪酬',
        'taxes_payable':                 '应交税费',
        'int_payable':                   '应付利息',
        'div_payable':                   '应付股利',
        'oth_payable':                   '其他应付款',
        'acc_exp':                       '预提费用',
        'deferred_inc':                  '递延收益',
        'st_bonds_payable':              '应付短期债券',
        'payable_to_reinsurer':          '应付分保账款',
        'rsrv_insur_cont':               '保险合同准备金',
        'acting_trading_sec':            '代理买卖证券款',
        'acting_uw_sec':                 '代理承销证券款',
        'non_cur_liab_due_1y':           '一年内到期的非流动负债',
        'oth_cur_liab':                  '其他流动负债',
        'total_cur_liab':                '流动负债合计',
        'bond_payable':                  '应付债券',
        'lt_payable':                    '长期应付款',
        'specific_payables':             '专项应付款',
        'estimated_liab':                '预计负债',
        'defer_tax_liab':                '递延所得税负债',
        'defer_inc_non_cur_liab':        '递延收益-非流动负债',
        'oth_ncl':                       '其他非流动负债',
        'total_ncl':                     '非流动负债合计',
        'depos_oth_bfi':                 '同业和其它金融机构存放款项',
        'deriv_liab':                    '衍生金融负债',
        'depos':                         '吸收存款',
        'agency_bus_liab':               '代理业务负债',
        'oth_liab':                      '其他负债',
        'prem_receiv_adva':              '预收保费',
        'depos_received':                '存入保证金',
        'ph_invest':                     '保户储金及投资款',
        'reser_une_prem':                '未到期责任准备金',
        'reser_outstd_claims':           '未决赔款准备金',
        'reser_lins_liab':               '寿险责任准备金',
        'reser_lthins_liab':             '长期健康险责任准备金',
        'indept_acc_liab':               '独立账户负债',
        'pledge_borr':                   '其中:质押借款',
        'indem_payable':                 '应付赔付款',
        'policy_div_payable':            '应付保单红利',
        'total_liab':                    '负债合计',
        'treasury_share':                '减:库存股',
        'ordin_risk_reser':              '一般风险准备',
        'forex_differ':                  '外币报表折算差额',
        'invest_loss_unconf':            '未确认的投资损失',
        'minority_int':                  '少数股东权益',
        'total_hldr_eqy_exc_min_int':    '股东权益合计(不含少数股东权益)',
        'total_hldr_eqy_inc_min_int':    '股东权益合计(含少数股东权益)',
        'total_liab_hldr_eqy':           '负债及股东权益总计',
        'lt_payroll_payable':            '长期应付职工薪酬',
        'oth_comp_income':               '其他综合收益',
        'oth_eqt_tools':                 '其他权益工具',
        'oth_eqt_tools_p_shr':           '其他权益工具(优先股)',
        'lending_funds':                 '融出资金',
        'acc_receivable':                '应收款项',
        'st_fin_payable':                '应付短期融资款',
        'payables':                      '应付款项',
        'hfs_assets':                    '持有待售的资产',
        'hfs_sales':                     '持有待售的负债',
        'update_flag':                   '更新标识',
    },

    'Finance.IncomeStatement': {
        'ts_code':                       'TS代码',
        'ann_date':                      '公告日期',
        'f_ann_date':                    '实际公告日期',
        'end_date':                      '报告期',
        'report_type':                   '报告类型',                           # 1合并报表; 2单季合并; 3调整单季合并表; 4调整合并报表; 5调整前合并报表; 6母公司报表; 7母公司单季表; 8 母公司调整单季表; 9母公司调整表; 10母公司调整前报表; 11调整前合并报表; 12母公司调整前报表;
        'comp_type':                     '公司类型',                           # 1一般工商业; 2银行; 3保险; 4证券
        'basic_eps':                     '基本每股收益',
        'diluted_eps':                   '稀释每股收益',
        'total_revenue':                 '营业总收入',
        'revenue':                       '营业收入',
        'int_income':                    '利息收入',
        'prem_earned':                   '已赚保费',
        'comm_income':                   '手续费及佣金收入',
        'n_commis_income':               '手续费及佣金净收入',
        'n_oth_income':                  '其他经营净收益',
        'n_oth_b_income':                '加:其他业务净收益',
        'prem_income':                   '保险业务收入',
        'out_prem':                      '减:分出保费',
        'une_prem_reser':                '提取未到期责任准备金',
        'reins_income':                  '其中:分保费收入',
        'n_sec_tb_income':               '代理买卖证券业务净收入',
        'n_sec_uw_income':               '证券承销业务净收入',
        'n_asset_mg_income':             '受托客户资产管理业务净收入',
        'oth_b_income':                  '其他业务收入',
        'fv_value_chg_gain':             '加:公允价值变动净收益',
        'invest_income':                 '加:投资净收益',
        'ass_invest_income':             '其中:对联营企业和合营企业的投资收益',
        'forex_gain':                    '加:汇兑净收益',
        'total_cogs':                    '营业总成本',
        'oper_cost':                     '减:营业成本',
        'int_exp':                       '减:利息支出',
        'comm_exp':                      '减:手续费及佣金支出',
        'biz_tax_surchg':                '减:营业税金及附加',
        'sell_exp':                      '减:销售费用',
        'admin_exp':                     '减:管理费用',
        'fin_exp':                       '减:财务费用',
        'assets_impair_loss':            '减:资产减值损失',
        'prem_refund':                   '退保金',
        'compens_payout':                '赔付总支出',
        'reser_insur_liab':              '提取保险责任准备金',
        'div_payt':                      '保户红利支出',
        'reins_exp':                     '分保费用',
        'oper_exp':                      '营业支出',
        'compens_payout_refu':           '减:摊回赔付支出',
        'insur_reser_refu':              '减:摊回保险责任准备金',
        'reins_cost_refund':             '减:摊回分保费用',
        'other_bus_cost':                '其他业务成本',
        'operate_profit':                '营业利润',
        'non_oper_income':               '加:营业外收入',
        'non_oper_exp':                  '减:营业外支出',
        'nca_disploss':                  '其中:减:非流动资产处置净损失',
        'total_profit':                  '利润总额',
        'income_tax':                    '所得税费用',
        'n_income':                      '净利润(含少数股东损益)',
        'n_income_attr_p':               '净利润(不含少数股东损益)',
        'minority_gain':                 '少数股东损益',
        'oth_compr_income':              '其他综合收益',
        't_compr_income':                '综合收益总额',
        'compr_inc_attr_p':              '归属于母公司(或股东)的综合收益总额',
        'compr_inc_attr_m_s':            '归属于少数股东的综合收益总额',
        'ebit':                          '息税前利润',
        'ebitda':                        '息税折旧摊销前利润',
        'insurance_exp':                 '保险业务支出',
        'undist_profit':                 '年初未分配利润',
        'distable_profit':               '可分配利润',
        'update_flag':                   '更新标识',                           # 0未修改; 1更正过
    },

    'Finance.CashFlowStatement': {
        'ts_code':                       'TS股票代码',
        'ann_date':                      '公告日期',
        'f_ann_date':                    '实际公告日期',
        'end_date':                      '报告期',
        'comp_type':                     '公司类型',
        'report_type':                   '报表类型',
        'net_profit':                    '净利润',
        'finan_exp':                     '财务费用',
        'c_fr_sale_sg':                  '销售商品、提供劳务收到的现金',
        'recp_tax_rends':                '收到的税费返还',
        'n_depos_incr_fi':               '客户存款和同业存放款项净增加额',
        'n_incr_loans_cb':               '向中央银行借款净增加额',
        'n_inc_borr_oth_fi':             '向其他金融机构拆入资金净增加额',
        'prem_fr_orig_contr':            '收到原保险合同保费取得的现金',
        'n_incr_insured_dep':            '保户储金净增加额',
        'n_reinsur_prem':                '收到再保业务现金净额',
        'n_incr_disp_tfa':               '处置交易性金融资产净增加额',
        'ifc_cash_incr':                 '收取利息和手续费净增加额',
        'n_incr_disp_faas':              '处置可供出售金融资产净增加额',
        'n_incr_loans_oth_bank':         '拆入资金净增加额',
        'n_cap_incr_repur':              '回购业务资金净增加额',
        'c_fr_oth_operate_a':            '收到其他与经营活动有关的现金',
        'c_inf_fr_operate_a':            '经营活动现金流入小计',
        'c_paid_goods_s':                '购买商品、接受劳务支付的现金',
        'c_paid_to_for_empl':            '支付给职工以及为职工支付的现金',
        'c_paid_for_taxes':              '支付的各项税费',
        'n_incr_clt_loan_adv':           '客户贷款及垫款净增加额',
        'n_incr_dep_cbob':               '存放央行和同业款项净增加额',
        'c_pay_claims_orig_inco':        '支付原保险合同赔付款项的现金',
        'pay_handling_chrg':             '支付手续费的现金',
        'pay_comm_insur_plcy':           '支付保单红利的现金',
        'oth_cash_pay_oper_act':         '支付其他与经营活动有关的现金',
        'st_cash_out_act':               '经营活动现金流出小计',
        'n_cashflow_act':                '经营活动产生的现金流量净额',
        'oth_recp_ral_inv_act':          '收到其他与投资活动有关的现金',
        'c_disp_withdrwl_invest':        '收回投资收到的现金',
        'c_recp_return_invest':          '取得投资收益收到的现金',
        'n_recp_disp_fiolta':            '处置固定资产、无形资产和其他长期资产收回的现金净额',
        'n_recp_disp_sobu':              '处置子公司及其他营业单位收到的现金净额',
        'stot_inflows_inv_act':          '投资活动现金流入小计',
        'c_pay_acq_const_fiolta':        '购建固定资产、无形资产和其他长期资产支付的现金',
        'c_paid_invest':                 '投资支付的现金',
        'n_disp_subs_oth_biz':           '取得子公司及其他营业单位支付的现金净额',
        'oth_pay_ral_inv_act':           '支付其他与投资活动有关的现金',
        'n_incr_pledge_loan':            '质押贷款净增加额',
        'stot_out_inv_act':              '投资活动现金流出小计',
        'n_cashflow_inv_act':            '投资活动产生的现金流量净额',
        'c_recp_borrow':                 '取得借款收到的现金',
        'proc_issue_bonds':              '发行债券收到的现金',
        'oth_cash_recp_ral_fnc_act':     '收到其他与筹资活动有关的现金',
        'stot_cash_in_fnc_act':          '筹资活动现金流入小计',
        'free_cashflow':                 '企业自由现金流量',
        'c_prepay_amt_borr':             '偿还债务支付的现金',
        'c_pay_dist_dpcp_int_exp':       '分配股利、利润或偿付利息支付的现金',
        'incl_dvd_profit_paid_sc_ms':    '其中:子公司支付给少数股东的股利、利润',
        'oth_cashpay_ral_fnc_act':       '支付其他与筹资活动有关的现金',
        'stot_cashout_fnc_act':          '筹资活动现金流出小计',
        'n_cash_flows_fnc_act':          '筹资活动产生的现金流量净额',
        'eff_fx_flu_cash':               '汇率变动对现金的影响',
        'n_incr_cash_cash_equ':          '现金及现金等价物净增加额',
        'c_cash_equ_beg_period':         '期初现金及现金等价物余额',
        'c_cash_equ_end_period':         '期末现金及现金等价物余额',
        'c_recp_cap_contrib':            '吸收投资收到的现金',
        'incl_cash_rec_saims':           '其中:子公司吸收少数股东投资收到的现金',
        'uncon_invest_loss':             '未确认投资损失',
        'prov_depr_assets':              '加:资产减值准备',
        'depr_fa_coga_dpba':             '固定资产折旧、油气资产折耗、生产性生物资产折旧',
        'amort_intang_assets':           '无形资产摊销',
        'lt_amort_deferred_exp':         '长期待摊费用摊销',
        'decr_deferred_exp':             '待摊费用减少',
        'incr_acc_exp':                  '预提费用增加',
        'loss_disp_fiolta':              '处置固定、无形资产和其他长期资产的损失',
        'loss_scr_fa':                   '固定资产报废损失',
        'loss_fv_chg':                   '公允价值变动损失',
        'invest_loss':                   '投资损失',
        'decr_def_inc_tax_assets':       '递延所得税资产减少',
        'incr_def_inc_tax_liab':         '递延所得税负债增加',
        'decr_inventories':              '存货的减少',
        'decr_oper_payable':             '经营性应收项目的减少',
        'incr_oper_payable':             '经营性应付项目的增加',
        'others':                        '其他',
        'im_net_cashflow_oper_act':      '经营活动产生的现金流量净额(间接法)',
        'conv_debt_into_cap':            '债务转为资本',
        'conv_copbonds_due_within_1y':   '一年内到期的可转换公司债券',
        'fa_fnc_leases':                 '融资租入固定资产',
        'end_bal_cash':                  '现金的期末余额',
        'beg_bal_cash':                  '减:现金的期初余额',
        'end_bal_cash_equ':              '加:现金等价物的期末余额',
        'beg_bal_cash_equ':              '减:现金等价物的期初余额',
        'im_n_incr_cash_equ':            '现金及现金等价物净增加额(间接法)',
        'update_flag':                   '更新标识',
    },
}


# -------------------------------------------------------- Prob --------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'finance_data_tushare_pro',
        'plugin_version': '0.0.0.1',
        'tags': ['tusharepro']
    }


def plugin_adapt(uri: str) -> bool:
    return uri in FIELDS.keys()


def plugin_capacities() -> list:
    return list(FIELDS.keys())


# ----------------------------------------------------------------------------------------------------------------------

# For the sake of "抱歉，您每分钟最多访问该接口60次"

delayer = Delayer(1000)


def __fetch_finance_data(**kwargs) -> pd.DataFrame:
    uri = kwargs.get('uri')
    result = check_execute_test_flag(**kwargs)

    if result is None:
        period = kwargs.get('period')

        ts_code = pickup_ts_code(kwargs)
        since, until = normalize_time_serial(period, default_since(), today())

        ts_since = since.strftime('%Y%m%d')
        ts_until = until.strftime('%Y%m%d')

        pro = ts.pro_api(TS_TOKEN)

        fields_list = list(FIELDS[uri].keys())
        field_joined = ','.join(fields_list)

        clock = Clock()
        delayer.delay()
        if uri == 'Finance.Audit':
            # Score 500; Update Na; No limit;
            result = pro.fina_audit(ts_code=ts_code, start_date=ts_since, end_date=ts_until, fields=field_joined)
        elif uri == 'Finance.BalanceSheet':
            # Score 500; Update Na; No limit;
            result = pro.balancesheet(ts_code=ts_code, start_date=ts_since, end_date=ts_until, fields=field_joined)
        elif uri == 'Finance.IncomeStatement':
            # Score 500; Update Na; No limit;
            result = pro.income(ts_code=ts_code, start_date=ts_since, end_date=ts_until, fields=field_joined)
        elif uri == 'Finance.CashFlowStatement':
            # Score 500; Update Na; No limit;
            result = pro.cashflow(ts_code=ts_code, start_date=ts_since, end_date=ts_until, fields=field_joined)
        else:
            result = None
        print('%s: [%s] - Network finished, time spending: %sms' % (uri, ts_code, clock.elapsed_ms()))
    check_execute_dump_flag(result, **kwargs)

    if result is not None:
        # result.rename(columns={'ts_code': 'stock_identity', 'end_date': 'period'}, inplace=True)
        result['period'] = result['end_date']
        result['stock_identity'] = result['ts_code']

        result['period'] = pd.to_datetime(result['period'])
        result['stock_identity'] = result['stock_identity'].str.replace('.SH', '.SSE')
        result['stock_identity'] = result['stock_identity'].str.replace('.SZ', '.SZSE')

        if uri is not None and uri == 'Finance.Audit':
            result['sign'] = result['audit_sign']
            result['agency'] = result['audit_agency']
            result['conclusion'] = result['audit_result']

            # result.rename(columns={'audit_result': 'conclusion',
            #                        'audit_agency': 'agency',
            #                        'audit_sign': 'sign'}, inplace=True)

    return result


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri in list(FIELDS.keys()):
        return __fetch_finance_data(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return FIELDS

