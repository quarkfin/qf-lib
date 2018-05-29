import pandas as pd

from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class RollingContractData(object):
    def __init__(self, prices_tms: PricesSeries, time_to_expiration_tms: pd.Series, returns_tms: SimpleReturnsSeries):
        self.prices_tms = prices_tms
        self.time_to_expiration_tms = time_to_expiration_tms
        self.returns_tms = returns_tms
