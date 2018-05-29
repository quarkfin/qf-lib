import pandas as pd

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class PricesDataFrame(QFDataFrame):

    @property
    def _constructor_sliced(self):
        from qf_lib.containers.series.prices_series import PricesSeries
        return PricesSeries

    @property
    def _constructor(self):
        return PricesDataFrame

    @property
    def _constructor_expanddim(self):
        return pd.Panel
