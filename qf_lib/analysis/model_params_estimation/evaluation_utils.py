from geneva_analytics.backtesting.alpha_models_testers.backtest_summary import BacktestSummary
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.document_exporting import Document, ParagraphElement, HeadingElement
from qf_lib.common.utils.document_exporting.element.new_page import NewPageElement
from qf_lib.common.utils.returns.sqn import sqn, avg_nr_of_trades_per1y, trade_based_cagr, trade_based_max_drawdown


def add_backtest_description(document: Document, backtest_result: BacktestSummary):
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
        document.add_element(ParagraphElement("Parameter #{} = [{}]".format(param_index + 1, param_list_str)))

    document.add_element(NewPageElement())


def evaluate_backtest(backtest_summary: BacktestSummary):
    ticker_eval_list = []
    for ticker in backtest_summary.tickers:
        for backtest_elem in backtest_summary.elements_list:

            parameters = backtest_elem.model_parameters

            all_trades = backtest_elem.trades_df
            trades_of_ticker = all_trades.loc[all_trades[TradeField.Ticker] == ticker]

            ticker_evaluation = TickerEvaluationResult()

            ticker_evaluation.ticker = ticker
            ticker_evaluation.parameters = parameters
            ticker_evaluation.SQN = sqn(trades_of_ticker)
            ticker_evaluation.avg_nr_of_trades_1Y = avg_nr_of_trades_per1y(trades_of_ticker,
                                                                           backtest_summary.start_date,
                                                                           backtest_summary.end_date)

            ticker_evaluation.annualised_return = trade_based_cagr(trades_of_ticker,
                                                                   backtest_summary.start_date,
                                                                   backtest_summary.end_date)

            ticker_evaluation.drawdown = trade_based_max_drawdown(trades_of_ticker)

            ticker_eval_list.append(ticker_evaluation)

    return ticker_eval_list


class TickerEvaluationResult(object):
    def __init__(self):
        self.ticker = None
        self.parameters = None

        self.SQN = None
        self.avg_nr_of_trades_1Y = None
        self.annualised_return = None
        self.drawdown = None
