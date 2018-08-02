from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class LogReturnsDataFrame(QFDataFrame):

    @property
    def _constructor_sliced(self):
        from qf_lib.containers.series.log_returns_series import LogReturnsSeries
        return LogReturnsSeries

    @property
    def _constructor(self):
        return LogReturnsDataFrame
