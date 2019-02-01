from datetime import datetime
from math import sqrt, exp

import numpy as np
from pandas import Int64Index

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


class AnalyticalCone:

    def __init__(self, series: QFSeries=None):
        if series is not None:
            self.series = series
            self.log_returns_tms = series.to_log_returns()

    def calculate_simple_cone(self, live_start_date: datetime, number_of_std: float)-> PricesSeries:
        """
        Creates a simple cone starting from a given date using the solution to the stochastic equation:
        S(t) = S(0)*exp( (mu-0.5*sigma^2)*t + sigma*N(0,1)*sqrt(t) )

        Parameters
        ----------
        number_of_std: corresponds to the randomness of the stochastic process. reflects number of standard deviations
            to get expected values for. For example 1.0 means 1 standard deviation above the expected value.
        live_start_date: datetime or string with date, corresponds to the cone start date

        Returns
        -------
        Price Series of expected values
        """

        is_log_tms = self.log_returns_tms.loc[self.log_returns_tms.index < live_start_date]
        oos_log_tms = self.log_returns_tms.loc[self.log_returns_tms.index >= live_start_date]

        mu = is_log_tms.mean()
        sigma = is_log_tms.std()

        days_oos = range(len(oos_log_tms) + 1)  # a list [0, 1, 2, ... N]
        initial_price = self.series.asof(is_log_tms.index[-1])   # price at last in-sample date

        # for each day OOS calculate the expected value at different point in time using the _get_expected_value()
        # function that gives expectation in single point in time.

        expected_values = list(map(lambda nr_of_days:
                                   self._get_expected_value(mu, sigma, initial_price, nr_of_days, number_of_std), days_oos))

        # We need to add last IS index value to connect the cone to the line. It will correspond to 0 days cone
        index = oos_log_tms.index.copy()
        index = index.insert(0, is_log_tms.index[-1])

        return PricesSeries(index=index, data=expected_values)

    def calculate_aggregated_cone(self, nr_of_days_to_evaluate: int, is_end_date: datetime, number_of_std: float) -> QFDataFrame:
        """
        Evaluates many simple cones and saves the end values of every individual simple cone.
        While using a simple cone (e.g. LineChart with Cone decorator) the results of the evaluation may be very
        different depending on the starting point. To be immune to this, calculate_aggregated_cone plots
        only the ends of simple cones which start  at 1 period, 2 periods, ..., n periods before the end of the series.
        The period length depends  on the frequency of the data provided for the chart. If it has daily frequency,
        then the length of one period will be 1 day.

        Parameters
        ----------
        number_of_std: corresponds to the randomness of the stochastic process. reflects number of standard deviations
            to get expected values for. For example 1.0 means 1 standard deviation above the expected value.
        nr_of_days_to_evaluate: max number of days in the past, from when all the cones are evaluated
        is_end_date: the end od in-sample date. Makes sure that in-sample doesn't move with the cone.

        Returns
        -------
        QFDataFrame: contains values corresponding to Strategy, Mean and Std. Values are indexed by number of days
            from which given cone was evaluated
        """

        nr_of_data_points = nr_of_days_to_evaluate + 1  # there is a point for 0 days at the beginning of the cone

        # if nr_of_days_to_evaluate is too large and goes into In-Sample, we need to reduce the value
        is_end_date_int_index = self.series.index.get_loc(is_end_date, method='pad')
        first_cone_index = len(self.log_returns_tms) - nr_of_data_points
        if first_cone_index < is_end_date_int_index:
            first_cone_index = is_end_date_int_index
            nr_of_data_points = len(self.log_returns_tms) - first_cone_index

        strategy_values = np.empty(nr_of_data_points)
        expected_values = np.empty(nr_of_data_points)

        mean_return, sigma = self._get_is_statistics(is_end_date)

        for i in range(nr_of_data_points):
            cone_start_idx = first_cone_index + i + 1

            # calculate total return of the strategy
            oos_log_returns = self.log_returns_tms[cone_start_idx:]
            total_strategy_return = exp(oos_log_returns.sum())  # 1 + percentage return

            # calculate expectation
            number_of_steps = len(oos_log_returns)
            starting_price = 1  # we take 1 as a base value
            total_expected_return = self._get_expected_value(mean_return, sigma, starting_price, number_of_steps, number_of_std)

            # writing to the array starting from the last array element and then moving towards the first one
            strategy_values[-i - 1] = total_strategy_return
            expected_values[-i - 1] = total_expected_return

        index = Int64Index(range(0, nr_of_data_points))

        strategy_values_tms = PricesSeries(index=index, data=strategy_values)
        expected_tms = QFSeries(index=index, data=expected_values)

        return QFDataFrame({
            'Strategy': strategy_values_tms,
            'Expectation': expected_tms,
        })

    def calculate_aggregated_cone_oos_only(self, oos_series: QFSeries, is_mean_return: float,
                                           is_sigma: float, number_of_std: float) -> QFDataFrame:
        """
        This functions does not need the IS history, only the IS statistics.

        Parameters
        ----------
        oos_series: series that is plotted on the cone - corresponds to the oos returns
        is_mean_return: mean daily return of the strategy In Sample
        is_sigma: std of daily returns of the strategy In Sample
        number_of_std: corresponds to the randomness of the stochastic process. reflects number of standard deviations
            to get expected values for. For example 1.0 means 1 standard deviation above the expected value.

        Returns
        -------
        QFDataFrame: contains values corresponding to Strategy, Mean and Std. Values are indexed by number of days
            from which given cone was evaluated
        """

        log_returns_tms = oos_series.to_log_returns()
        nr_of_data_points = oos_series.size

        strategy_values = np.empty(nr_of_data_points)
        expected_values = np.empty(nr_of_data_points)

        for i in range(nr_of_data_points):
            cone_start_idx = i + 1

            # calculate total return of the strategy
            oos_log_returns = log_returns_tms[cone_start_idx:]
            total_strategy_return = exp(oos_log_returns.sum())  # 1 + percentage return

            # calculate expectation
            number_of_steps = len(oos_log_returns)
            starting_price = 1  # we take 1 as a base value
            total_expected_return = self._get_expected_value(is_mean_return, is_sigma, starting_price,
                                                             number_of_steps, number_of_std)

            # writing to the array starting from the last array element and then moving towards the first one
            strategy_values[-i - 1] = total_strategy_return
            expected_values[-i - 1] = total_expected_return

        index = Int64Index(range(0, nr_of_data_points))

        strategy_values_tms = PricesSeries(index=index, data=strategy_values)
        expected_tms = QFSeries(index=index, data=expected_values)

        return QFDataFrame({
            'Strategy': strategy_values_tms,
            'Expectation': expected_tms,
        })

    def _get_is_statistics(self, is_end_date: datetime) -> (float, float):
        """
        Returns the mean return and standard deviation of return In-Sample
        """
        in_sample_log_returns = self.log_returns_tms[self.log_returns_tms.index <= is_end_date]
        mean_return = in_sample_log_returns.mean()
        sigma = in_sample_log_returns.std()
        return mean_return, sigma

    @staticmethod
    def _get_expected_value(mu, sigma, starting_price, number_of_steps, random_element):
        """
        For the mu and sigma calculated based on log returns:
            S(t) = S(0)*exp( (mu-0.5*sigma^2)*t + sigma*N(0,1)*sqrt(t) )
        Parameters
        ----------
        mu - mean of the distribution of returns
        sigma - standard deviation of the returns
        starting_price - price of the stock at the begining of the cone
        number_of_steps - number of
        random_element - corresponds to the N(0,1). is expressed in number of standard deviations.
            Use 1 to model 1std up move,
            Use 0 to model expected vale of the stock

        Returns
        -------
        Expected value of the stock after number_of_steps given the input parameters
        """
        deterministic_part = (mu - 0.5 * pow(sigma, 2)) * number_of_steps
        random_part = sigma * random_element * sqrt(number_of_steps)
        return starting_price * exp(deterministic_part + random_part)
