from datetime import datetime, timedelta

import matplotlib.pyplot as plt

from qf_common.config.ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.indicators.market_stress_indicator_us import MarketStressIndicator
from qf_lib.plotting.charts.histogram_chart import HistogramChart
from qf_lib.plotting.helpers.create_line_chart import create_line_chart


def main():
    tickers = [BloombergTicker('VIX Index'),       # Volatility: US Equity
               BloombergTicker('MOVE Index'),      # Volatility: Bonds
               BloombergTicker('JPMVXYGL Index'),  # Volatility: Global FX
               BloombergTicker('CSI BARC Index'),  # Corporate Spread: HY
               BloombergTicker('CSI BBB Index'),   # Corporate Spread: BBB
               BloombergTicker('CSI A Index'),     # Corporate Spread: A
               BloombergTicker('BASPTDSP Index')]  # Liquidity: TED Spread
    weights = [1, 1, 1, 1, 1, 1, 3]
    data_provider = container.resolve(GeneralPriceProvider)  # type: GeneralPriceProvider

    msi = MarketStressIndicator(tickers, weights, data_provider)

    start_date = str_to_date('2010-01-01')
    end_date = datetime.now()
    years_rolling = 2
    step = 5

    stress_indicator_tms = msi.get_indicator(years_rolling, start_date, end_date, step)

    fig_size = (10, 5)

    # stress_indicator_tms = cached_value(_get_indicator, indicator_cache_path)  # type: QFSeries
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


if __name__ == '__main__':
    main()

