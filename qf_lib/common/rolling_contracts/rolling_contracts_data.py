import pandas as pd

from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class RollingContractData(object):
    def __init__(self, prices_df: PricesDataFrame, time_to_expiration_tms: pd.Series, returns_tms: SimpleReturnsSeries):
        """
        Parameters
        ----------
        prices_df
            DataFrame for a certain contract (e.g. 1-month contract) with Open, High, Low, Close, Volume as columns.
            It is indexed with time.
        time_to_expiration_tms
            Timeseries showing in how much time the currently held real contract will expire
        returns_tms
            returns of the
        """
        self.prices_df = prices_df
        self.time_to_expiration_tms = time_to_expiration_tms
        self.returns_tms = returns_tms
