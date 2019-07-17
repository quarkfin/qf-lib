from math import sqrt
from typing import List, Sequence

from qf_lib.backtesting.fast_alpha_model_tester.backtest_summary import BacktestSummary
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.returns.sqn import sqn_for100trades, avg_nr_of_trades_per1y, trade_based_cagr, \
    trade_based_max_drawdown
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement


def add_backtest_description(document: Document, backtest_result: BacktestSummary, param_names: List[str]):
    """
    Adds verbal description of the backtest to the document. The description will be placed on a single page.
    """

    document.add_element(ParagraphElement("\n"))
    document.add_element(HeadingElement(1, "Model: {}".format(backtest_result.backtest_name)))
    document.add_element(ParagraphElement("\n"))

    document.add_element(HeadingElement(2, "Tickers tested in this study: "))
    ticker_str = "\n".join([ticker.as_string() for ticker in backtest_result.tickers])
    document.add_element(ParagraphElement(ticker_str))
    document.add_element(ParagraphElement("\n"))

    document.add_element(HeadingElement(2, "Dates of the backtest"))
    document.add_element(ParagraphElement("Backtest start date: {}"
                                          .format(date_to_str(backtest_result.start_date))))
    document.add_element(ParagraphElement("Backtest end date: {}"
                                          .format(date_to_str(backtest_result.end_date))))

    document.add_element(ParagraphElement("\n"))

    document.add_element(HeadingElement(2, "Parameters Tested"))
    for param_index, param_list in enumerate(backtest_result.parameters_tested):
        param_list_str = ", ".join(map(str, param_list))
        document.add_element(ParagraphElement("{} = [{}]".format(param_names[param_index], param_list_str)))

    document.add_element(NewPageElement())


class BacktestSummaryEvaluator(object):
    def __init__(self, backtest_summary: BacktestSummary):
        self.backtest_summary = backtest_summary

        self.params_backtest_summary_elem_dict = {}
        for elem in backtest_summary.elements_list:
            self.params_backtest_summary_elem_dict[elem.model_parameters] = elem

    def evaluate_params_for_tickers(self, parameters: tuple, tickers: Sequence[Ticker]):
        trades_of_tickers = self._select_trades_of_tickers(parameters, tickers)
        return self._evaluate_single_trades_df(parameters, tickers, trades_of_tickers)

    def _evaluate_single_trades_df(self, parameters, tickers_to_be_used, trades_of_tickers):
        ticker_evaluation = TradesEvaluationResult()
        ticker_evaluation.ticker = tickers_to_be_used
        ticker_evaluation.parameters = parameters
        ticker_evaluation.sqn_per100trades = sqn_for100trades(trades_of_tickers)
        avg_nr_of_trades = avg_nr_of_trades_per1y(trades_of_tickers, self.backtest_summary.start_date,
                                                  self.backtest_summary.end_date)
        ticker_evaluation.avg_nr_of_trades_1Y = avg_nr_of_trades
        ticker_evaluation.annualised_return = trade_based_cagr(trades_of_tickers,
                                                               self.backtest_summary.start_date,
                                                               self.backtest_summary.end_date)
        ticker_evaluation.drawdown = trade_based_max_drawdown(trades_of_tickers)

        if avg_nr_of_trades > 5:  # for clarity of the chart remove values that do not show enough trading
            ticker_evaluation.sqn_per_avg_nr_trades = ticker_evaluation.sqn_per100trades / 10 * sqrt(avg_nr_of_trades)

        return ticker_evaluation

    def _select_trades_of_tickers(self, parameters: tuple, tickers: Sequence[Ticker]):
        backtest_elem = self.params_backtest_summary_elem_dict[parameters]
        all_trades = backtest_elem.trades_df

        # select trades of provided tickers only
        trades_of_tickers = all_trades.loc[all_trades[TradeField.Ticker].isin(tickers)]
        return trades_of_tickers


class TradesEvaluationResult(object):
    def __init__(self):
        self.ticker = None
        self.parameters = None

        self.sqn_per_avg_nr_trades = None
        self.sqn_per100trades = None
        self.avg_nr_of_trades_1Y = None
        self.annualised_return = None
        self.drawdown = None
