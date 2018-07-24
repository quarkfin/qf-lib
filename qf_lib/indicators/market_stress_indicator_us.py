import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from pandas import DataFrame

from qf_common.config import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.charts.histogram_chart import HistogramChart
from qf_lib.plotting.helpers.create_line_chart import create_line_chart

tickers = [BloombergTicker('VIX Index'),       # Volatility: US Equity
           BloombergTicker('MOVE Index'),      # Volatility: Bonds
           BloombergTicker('JPMVXYGL Index'),  # Volatility: Global FX
           BloombergTicker('CSI BARC Index'),  # Corporate Spread: HY
           BloombergTicker('CSI BBB Index'),   # Corporate Spread: BBB
           BloombergTicker('CSI A Index'),     # Corporate Spread: A
           BloombergTicker('BASPTDSP Index')]  # Liquidity: TED Spread

weights = [1, 1, 1, 1, 1, 1, 3]
start_date = str_to_date('2000-01-01')
end_date = datetime.now()
fig_size = (10, 5)
years_rolling = 4


def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    data_cache_path = os.path.join(dir_path, 'stress_indicator_2000.cache')
    indicator_cache_path = os.path.join(dir_path, 'stress_indicator_2000_tms_{}Y.cache'.format(years_rolling))

    def _get_indicator():
        def _download_data():
            data_provider = container.resolve(GeneralPriceProvider)  # type: GeneralPriceProvider
            data = data_provider.get_price(tickers, PriceField.Close, start_date, end_date)
            return data

        data = cached_value(_download_data, data_cache_path)  # type: QFDataFrame
        data = data.fillna(method='ffill')
        # data = data.dropna() # this line can be enabled but it will shift starting point by the years_rolling

        stress_indicator_tms = data.rolling_time_window(window_length=252*years_rolling, step=1,
                                                        func=rolling_stress_indicator)
        return stress_indicator_tms

    stress_indicator_tms = cached_value(_get_indicator, indicator_cache_path)  # type: QFSeries
    chart = create_line_chart([stress_indicator_tms], ['Stress Indicator'], "Stress Indicator US")
    chart.plot(figsize=fig_size)

    no_none_indicator_tms = stress_indicator_tms.dropna()
    histogram = HistogramChart(no_none_indicator_tms, best_fit=False, bins=100)
    histogram.plot(figsize=fig_size)

    # Get SPX Index
    data_provider = container.resolve(GeneralPriceProvider)  # type: GeneralPriceProvider
    spx = BloombergTicker('SPX Index')
    spx_index_tms = data_provider.get_price(spx, PriceField.Close, no_none_indicator_tms.first_valid_index(), end_date)
    spx_returns = spx_index_tms.to_simple_returns()

    # Calculate managed series
    managed_series = SimpleReturnsSeries()
    for date, ret in spx_returns.iteritems():
        risk_value = no_none_indicator_tms.asof(date-timedelta(days=2))

        leverage = 1
        if risk_value > 0.35:
            leverage = 0.66
        if risk_value > 1.5:
            leverage = 0.33

        managed_ret = ret * leverage
        managed_series[date] = managed_ret

    # Plot managed and pure SPX series
    chart = create_line_chart([spx_returns.to_prices(), managed_series.to_prices()],
                              ['SPX Index', "SPX with Stress Indicator"])
    chart.plot(figsize=fig_size)
    plt.show(block=True)


def rolling_stress_indicator(data_frame_window: QFDataFrame):
    zscore_df = DataFrame()
    for name, series in data_frame_window.items():
        zscore_df[name] = (series - series.mean()) / series.std()

    last_row = zscore_df.tail(1)
    result = last_row.dot(weights)  # produces a weighted sum of the z-scored values
    result = result[0] / sum(weights)  # result was a single element series, return the value only
    return result


if __name__ == '__main__':
    main()

