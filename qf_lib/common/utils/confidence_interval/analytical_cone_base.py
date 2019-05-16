import abc
from datetime import datetime
from math import sqrt, exp

from qf_lib.containers.series.log_returns_series import LogReturnsSeries


class AnalyticalConeBase(metaclass=abc.ABCMeta):

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
