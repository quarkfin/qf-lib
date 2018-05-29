import pandas as pd

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class SimpleReturnsDataFrame(QFDataFrame):

    @property
    def _constructor_sliced(self):
        from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
        return SimpleReturnsSeries

    @property
    def _constructor(self):
        return SimpleReturnsDataFrame

    @property
    def _constructor_expanddim(self):
        return pd.Panel

    def aggregate_by_year(self):
        # TODO make get_aggregate_returns accept DataFrames and remove this function
        # or create get_aggregate_returns_for_data_frame
        from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
        from qf_lib.common.enums.frequency import Frequency

        def agg_series_by_year(series):
            return get_aggregate_returns(series=series, convert_to=Frequency.YEARLY)

        annual_returns_df = self.apply(agg_series_by_year, axis=0)
        return annual_returns_df
