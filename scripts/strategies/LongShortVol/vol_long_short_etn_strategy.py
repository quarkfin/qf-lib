from datetime import timedelta
from math import sqrt

from qf_lib.backtesting.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.log_returns_series import LogReturnsSeries
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


class VolLongShortUsingETN(object):
    def __init__(self, backtest_trading_session: BacktestTradingSession, use_stop_loss=False):
        self.data_handler = backtest_trading_session.data_handler
        self.order_factory = backtest_trading_session.order_factory

        self.timer = backtest_trading_session.timer
        self.broker = backtest_trading_session.broker

        notifiers = backtest_trading_session.notifiers
        notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

        if use_stop_loss:
            raise NotImplementedError("Using stop Loss is not yet available")

        self.use_stop_loss = use_stop_loss
        self.vix_ticker = BloombergTicker("VIX Index")
        self.spx_ticker = BloombergTicker("SPX Index")
        # self.vix_ticker = QuandlTicker("MSFT", 'WIKI')
        # self.spx_ticker = QuandlTicker("AAPL", 'WIKI')

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self._calculate_signals()

    def on_market_close(self):
        self._check_stop_loss()

    def _calculate_signals(self):
        vxx_ticker = BloombergTicker('VXX US Equity')
        xiv_ticker = BloombergTicker('XIV US Equity')
        # vxx_ticker = QuandlTicker("MSFT", 'WIKI')
        # xiv_ticker = QuandlTicker("AAPL", 'WIKI')

        volWindowSize = 3
        indicatorWindowSize = 2
        threshold = -2
        maxVixLevel = float("inf")

        allocation = self._calculate_signal(threshold, maxVixLevel, volWindowSize, indicatorWindowSize)

        target_weight_dict = {vxx_ticker: allocation[0], xiv_ticker: allocation[1]}

        order_list = self.order_factory.order_target_percent(target_weight_dict)

        self.broker.place_orders(order_list)

    def _calculate_indicator(self, volWindowSize, indicatorWindowSize) -> float:
        # indicatorWindowSize - is an integer. indicatorWindowSize >= 2
        # indicator = indicatorWindowSize day average of (VIX - (volWindowSize day historial vol of SPX * 100))

        end_date = self.timer.now()
        start_date = end_date - timedelta(days=50)
        tickers = [self.spx_ticker, self.vix_ticker]
        price_df = self.data_handler.get_price(tickers, PriceField.Close, start_date, end_date)

        spx_log_tms = price_df[self.spx_ticker].to_log_returns()

        def vol_func(window: LogReturnsSeries) -> float:
            return get_volatility(window, Frequency.DAILY) * 100  # vol is in % -> multiply by 100
        rolling_spx_vol = spx_log_tms.rolling_window(volWindowSize, func=vol_func)

        selected_realised_vol = rolling_spx_vol.tail(indicatorWindowSize)
        selected_vix_values = price_df[self.vix_ticker].tail(indicatorWindowSize)

        # finally, calculate value of the indicator for the next day
        diff = selected_vix_values - selected_realised_vol  # type: QFSeries
        indicator = diff.mean()
        return indicator

    def _calculate_signal(self, threshold, maxVixLevel, volWindowSize, indicatorWindowSize) -> (float, float):
        # invest in VXX or XIV depending on the indicator and threshold
        # the signal should be used to invest the following day

        # threshold   - is a value that corresponds to indicator.
        # maxVixLevel - is a maximum level of VIX Index. If VIX is above this level we go to cash.
        # message     - is a text representation of the strategy signal
        # allocation  - is a vector  allocation(0) corresponds to VXX (VIX),
        #                            allocation(1) corresponds to XIV (Inverse VIX)

        indicator = self._calculate_indicator(volWindowSize, indicatorWindowSize)
        current_vix_price = self.data_handler.get_last_available_price(self.vix_ticker)
        allocation = [0, 0]

        # check if we can trade based on VIX Index level.
        if current_vix_price <= maxVixLevel:
            if indicator >= threshold:
                # 'Normal' situation: Implied volatility is above realised
                # Invest in Inverse VIX (XIV)
                allocation[0] = 0     # VXX
                allocation[1] = 1     # XIV
            elif indicator < threshold:
                # Realised Volatility spikes, invest in VIX Index (VXX)
                allocation[0] = 1     # VXX
                allocation[1] = 0     # XIV
            else:  # indicator is NaN
                raise ValueError('CalculateSignal:incorrectIndicator')

        return allocation

    def _calculate_stop_loss(self, nrOfDaysOfVIX, stopLossParameter, maxStopLoss):
        # stopLoss = max[(-0.22) * sqrt(20D MA(VIX) * 20 std(VIX) ), -3]
        # stopLoss is expressed in % and refers to the previous close or open price is reallocation

        end_date = self.timer.now()
        start_date = end_date - timedelta(days=50)

        vix_tms = self.data_handler.get_price(self.vix_ticker, PriceField.Close, start_date, end_date)
        selected_vix_tms = vix_tms.tail(nrOfDaysOfVIX)  # type: PricesSeries

        mean_price = selected_vix_tms.mean()
        selected_vix_returns = selected_vix_tms.to_simple_returns()
        vol = selected_vix_returns.std()  # TODO: consider using volatility
        stopLoss = stopLossParameter * sqrt(mean_price * vol)
        stopLoss = max(stopLoss, maxStopLoss)
        return stopLoss

    def _check_stop_loss(self):
        nrOfDaysOfVIX = 20
        stopLossParameter = -0.22
        maxStopLoss = -3
        stop_loss = self._calculate_stop_loss(nrOfDaysOfVIX, stopLossParameter, maxStopLoss)
        stop_loss_multiplier = (stop_loss / 100) + 1  # expressed as a number, not %

        # TODO: use stop loss
