from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class SimpleReturnsDataFrame(QFDataFrame):

    @property
    def _constructor_sliced(self):
        from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
        return SimpleReturnsSeries

    @property
    def _constructor(self):
        return SimpleReturnsDataFrame

    def aggregate_by_year(self):
        from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
        from qf_lib.common.enums.frequency import Frequency

        def agg_series_by_year(series):
            return get_aggregate_returns(series=series, convert_to=Frequency.YEARLY)

        annual_returns_df = self.apply(agg_series_by_year, axis=0)
        return annual_returns_df
