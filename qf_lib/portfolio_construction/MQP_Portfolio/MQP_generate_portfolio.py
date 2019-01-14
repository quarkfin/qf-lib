import os
from datetime import timedelta, datetime
from os.path import join

import numpy as np

from qf_common.config import ioc
from qf_common.config.ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.data_cleaner import DataCleaner
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.portfolio_construction.MQP_Portfolio.MQP_settings import MQPSettings
from qf_lib.portfolio_construction.portfolio_models.multifactor_portfolio import MultiFactorPortfolio, \
    PortfolioParameters
from qf_lib.settings import Settings


allocation_date = datetime.now()
stress_level = 1  # to be passed from stress level calculation'
riy_ticker = BloombergTicker('RIY Index')
field = 'INDX_MEMBERS'


def remove_tickers(riy_ticker_names, tickers_to_remove):
    for name in riy_ticker_names:
        for name_to_remove in tickers_to_remove:
            if name_to_remove in name:
                riy_ticker_names.remove(name)
                tickers_to_remove.remove(name_to_remove)
                print("\tTicker {} removed from list".format(name))
                break
    if len(tickers_to_remove) > 0:
        print("\tSignatures {} were not found in the list of Tickers.".format(tickers_to_remove))


def create_tickers(riy_ticker_names):
    tickers_universe = []
    for elem in riy_ticker_names:
        ticker_name = elem + " Equity"
        ticker = BloombergTicker(ticker_name)
        tickers_universe.append(ticker)
    return tickers_universe


def calculate_returns(tickers_universe, allocation_date, riy_ticker) -> SimpleReturnsDataFrame:
    # take a bit more history than needed and then cut out what is left
    end_date = allocation_date - timedelta(days=1)
    nr_of_days_to_go_back = np.floor(365 / MQPSettings.frequency.value * MQPSettings.window_size * 1.2)
    start_date = end_date - timedelta(days=nr_of_days_to_go_back)

    riy_close_tms = data_provider.get_price(riy_ticker, PriceField.Close, start_date, end_date).dropna()
    riy_close_tms.name = riy_ticker
    riy_rets_tms = riy_close_tms.to_simple_returns()
    riy_rets_tms = riy_rets_tms.tail(MQPSettings.window_size)

    close_prices_for_all_tickers = data_provider.get_price(tickers_universe, PriceField.Close, start_date, end_date)
    all_returns_df = close_prices_for_all_tickers.reindex(riy_rets_tms.index)
    all_returns_df = all_returns_df.to_simple_returns()

    data_cleaner = DataCleaner(all_returns_df, MQPSettings.proxy_threshold)
    all_returns_df = data_cleaner.proxy_using_regression(riy_rets_tms, SimpleReturnsSeries)
    return all_returns_df


def calculate_portfolio_tickers_and_weights(returns_df, stress_level):
    weights = MQPSettings.weights[stress_level]
    parameters = PortfolioParameters(*weights)
    portfolio = MultiFactorPortfolio(returns_df, parameters)
    return portfolio.get_weights()


data_provider = ioc.container.resolve(BloombergDataProvider)  # type: BloombergDataProvider
riy_ticker_names = data_provider.get_tabular_data(riy_ticker, field)
print("1a. Ticker names downloaded.")

tickers_to_remove = ['RHT ', 'DNB ', 'VVC ', 'FCE/A ', 'AET ']  # put a space after the ticker!
remove_tickers(riy_ticker_names, tickers_to_remove)
print("1b. Excess Tickers removed from list.")

tickers_universe = create_tickers(riy_ticker_names)
returns_df = calculate_returns(tickers_universe, allocation_date, riy_ticker)
print("2. DataFrame of Ticker returns calculated.")

portfolio_output = calculate_portfolio_tickers_and_weights(returns_df, stress_level)
portfolio_output = portfolio_output[portfolio_output > 0.01]
print("3. Portfolio Tickers and weights generated (optimisation).")
print(portfolio_output)

portfolio_output.index = [ticker.as_string() for ticker in portfolio_output.index]
settings = container.resolve(Settings)
file_name_template = datetime.now().strftime("%Y_%m_%d-%H%M {}".format("portfolio_output" + ".xlsx"))
xlx_file_path = join(settings.output_directory, file_name_template)
# Make sure an old version of this file is removed.
if os.path.exists(xlx_file_path):
    os.remove(xlx_file_path)
xlx_exporter = ExcelExporter(settings)
xlx_exporter.export_container(portfolio_output, xlx_file_path, include_column_names=True)
print("4. Portfolio Tickers and weights exported to {}.".format(file_name_template))

