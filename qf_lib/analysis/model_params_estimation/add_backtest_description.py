from geneva_analytics.backtesting.alpha_models_testers.backtest_summary import BacktestSummary
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.document_exporting import Document, ParagraphElement, HeadingElement
from qf_lib.common.utils.document_exporting.element.new_page import NewPageElement


def add_backtest_description(document: Document, backtest_result: BacktestSummary):
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

    document.add_element(HeadingElement(2, "Parameters Tested"))
    for param_index, param_list in enumerate(backtest_result.parameters_tested):
        param_list_str = ", ".join(map(str, param_list))
        document.add_element(ParagraphElement("Parameter #{} = [{}}".format(param_index + 1, param_list_str)))

    document.add_element(NewPageElement())