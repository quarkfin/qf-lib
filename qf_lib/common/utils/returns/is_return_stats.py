from qf_lib.containers.series.qf_series import QFSeries


class InSampleReturnStats(object):
    """
    Stores values of stats used to build confidence interval (Cone Chart)
    """

    def __init__(self, mean_log_ret: float=None, std_of_log_ret:float=None):
        """

        Parameters
        ----------
        mean_log_ret
            mean log return expressed in the frequency of data samples (usually daily)
        std_of_log_ret
            std of log returns expressed in the frequency of data samples (usually daily)
        """
        self.mean_log_ret = mean_log_ret
        self.std_of_log_ret = std_of_log_ret

    def __str__(self):
        return "mean log return: {}, std of log returns: {}".format(self.mean_log_ret, self.std_of_log_ret)


    @staticmethod
    def get_stats_from_tms(series: QFSeries):
        log_ret_tms = series.to_log_returns()
        return InSampleReturnStats(log_ret_tms.mean(), log_ret_tms.std())
