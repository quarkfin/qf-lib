from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker


class MQPSettings(object):

    benchmark_ticker = BloombergTicker('RIY Index')
    frequency = Frequency.DAILY
    window_size = 126
    min_allocation = 0.01
    max_allocation = 0.05  # max allocation into a single asset
    proxy_threshold = 0.03  # how much we are willing to proxy

    weights = {1: [0.0001, 0.33, 0.22, 0.45],  # low risk
               2: [0.0001, 0.25, 0.25, 0.50],  # medium risk
               3: [0.0001, 0.12, 0.29, 0.59]}  # high risk

    portfolio_allocation = [1.00, 0.75, 0.50]
