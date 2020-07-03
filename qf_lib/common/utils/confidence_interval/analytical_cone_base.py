#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import abc
from math import sqrt, exp

from qf_lib.containers.series.prices_series import PricesSeries


class AnalyticalConeBase(metaclass=abc.ABCMeta):

    @staticmethod
    def get_expected_value(mu, sigma, starting_price, number_of_steps, random_element) -> float:
        """
        For the mu and sigma calculated based on log returns:
            S(t) = S(0)*exp( (mu-0.5*sigma^2)*t + sigma*N(0,1)*sqrt(t))

        Parameters
        ----------
        mu
            mean of the distribution of returns
        sigma
            standard deviation of the returns
        starting_price
            price of the stock at the beginning of the cone
        number_of_steps
            horizon for which the expected value is calculated
        random_element
            corresponds to the N(0,1). is expressed in number of standard deviations.
            Use 1 to model 1std up move,
            Use 0 to model expected vale of the stock

        Returns
        -------
        float
            Expected value of the stock after number_of_steps given the input parameters
        """
        deterministic_part = (mu - 0.5 * pow(sigma, 2)) * number_of_steps
        random_part = sigma * random_element * sqrt(number_of_steps)
        return starting_price * exp(deterministic_part + random_part)

    def calculate_simple_cone_for_process(self, mu: float, sigma: float, number_of_std: float, number_of_steps: int,
                                          starting_value=1) -> PricesSeries:
        """
        Creates a simple cone starting from a given date using the solution to the stochastic equation:
        S(t) = S(0)*exp( (mu-0.5*sigma^2)*t + sigma*N(0,1)*sqrt(t) )

        Parameters
        ----------
        mu
            mean return of the process. expressed in the frequency of samples (not annualised)
        sigma
            std of returns of the process. expressed in the frequency of samples (not annualised)
        number_of_std
            corresponds to the randomness of the stochastic process. reflects number of standard deviations
            to get expected values for. For example 1.0 means 1 standard deviation above the expected value.
        number_of_steps
            length of the cone that we are creating
        starting_value
            corresponds to the starting price of the instrument

        Returns
        -------
        PriceSeries
            expected values
        """

        steps = range(number_of_steps + 1)  # a list [0, 1, 2, ... N]

        # for each day OOS calculate the expected value at different point in time using the _get_expected_value()
        # function that gives expectation in single point in time.
        expected_values = list(map(
            lambda nr_of_days: self.get_expected_value(mu, sigma, starting_value, nr_of_days, number_of_std), steps))

        return PricesSeries(index=steps, data=expected_values)
