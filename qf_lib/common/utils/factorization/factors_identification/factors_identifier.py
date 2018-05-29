import abc

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class FactorsIdentifier(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def select_best_factors(self, regressors_df: QFDataFrame, analysed_tms: QFSeries) -> QFDataFrame:
        raise NotImplementedError()
