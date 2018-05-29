from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class DataModelInput(object):
    """ Class storing an input data from which FactorizationDataModel is built. """

    def __init__(self, regressors_df: SimpleReturnsDataFrame, analysed_tms: SimpleReturnsSeries, frequency: Frequency,
                 is_fit_intercept: bool):
        """
        Parameters
        ----------
        regressors_df
            dataframe of regressors which should be included in the final model
        analysed_tms
            timeseries of returns which should be modeled using regressors
        frequency
            frequency of data used in both regressors and analysed timeseries
        is_fit_intercept
            True if the model should contain the intercept; False otherwise
        """
        assert len(regressors_df.index) == len(analysed_tms)

        self.regressors_df = regressors_df
        self.analysed_tms = analysed_tms
        self.is_fit_intercept = is_fit_intercept
        self.frequency = frequency
