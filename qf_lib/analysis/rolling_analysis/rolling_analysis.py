from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class RollingAnalysisFactory(object):
    @classmethod
    def calculate_analysis(cls, strategy_tms: QFSeries, benchmark_tms: QFSeries):
        """
        Calculates the rolling table for provided timeseries
        """
        rows = list()
        windows = [(6 * 21, "6 Months"), (252, "1 Year"),
                   (252 * 2, "2 Years"), (252 * 5, "5 Years")]

        # Ensure that this data is daily.
        df = PricesDataFrame()
        strategy_name = strategy_tms.name
        benchmark_name = benchmark_tms.name
        df[strategy_name] = strategy_tms.to_prices()
        df[benchmark_name] = benchmark_tms.to_prices()
        df.fillna(method='ffill', inplace=True)

        for window_info in windows:
            window = window_info[0]

            # if window is too big for the strategy then skip it
            if window >= int(df.shape[0] / 2):
                continue

            step = int(window * 0.2)

            strategy_rolling = df[strategy_name].rolling_window(window, lambda x: x.total_cumulative_return(), step)
            benchmark_rolling = df[benchmark_name].rolling_window(window, lambda x: x.total_cumulative_return(), step)

            outperforming = strategy_rolling > benchmark_rolling
            percentage_outperforming = len(strategy_rolling[outperforming]) / len(strategy_rolling)

            dto = RollingAnalysisDTO(
                period=window_info[1],
                strategy_average=strategy_rolling.mean(),
                strategy_worst=strategy_rolling.min(),
                strategy_best=strategy_rolling.max(),
                benchmark_average=benchmark_rolling.mean(),
                benchmark_worst=benchmark_rolling.min(),
                benchmark_best=benchmark_rolling.max(),
                percentage_difference=percentage_outperforming
            )
            rows.append(dto)
        return rows


class RollingAnalysisDTO(object):
    def __init__(self, period, strategy_average, strategy_worst, strategy_best, benchmark_average, benchmark_worst,
                 benchmark_best, percentage_difference):
        self.period = period
        self.strategy_average = strategy_average
        self.strategy_worst = strategy_worst
        self.strategy_best = strategy_best
        self.benchmark_average = benchmark_average
        self.benchmark_worst = benchmark_worst
        self.benchmark_best = benchmark_best
        self.percentage_difference = percentage_difference
