class RollingWindowsEstimator(object):
    """
    Class for estimating parameters of rolling windows.
    """

    @classmethod
    def estimate_rolling_window_size(cls, container):
        """
        Estimates the size of the rolling window based on the number of samples.

        Parameters
        ----------
        container: QFDataFrame or QFSeries
            container with data analysed using rolling window

        Returns
        -------
        window_size: int
            the calculated size of the rolling window
        """
        num_of_samples = container.shape[0]

        if 12 <= num_of_samples < 20:
            window_size = 3
        elif 20 <= num_of_samples < 50:
            window_size = 6
        elif 50 <= num_of_samples < 120:
            window_size = 12
        elif 120 <= num_of_samples < 300:
            window_size = 30
        elif 300 <= num_of_samples < 500:
            window_size = 75
        elif 500 <= num_of_samples:
            window_size = 125
        else:
            raise ValueError("Too few samples to estimate a rolling window's size.")

        return window_size

    @classmethod
    def estimate_rolling_window_step(cls, container):
        """
        Estimates the step of the rolling window based on the number of samples.

        Parameters
        ----------
        container: QFDataFrame or QFSeries
            container with data analysed using rolling window

        Returns
        -------
        window_step: int
            the calculated step (shift) of the rolling window
        """
        num_of_samples = container.shape[0]

        if 12 <= num_of_samples < 120:
            step = 2
        elif 120 <= num_of_samples < 500:
            step = 10
        elif 500 <= num_of_samples < 1500:
            step = 20
        elif 1500 <= num_of_samples:
            step = 50
        else:
            raise ValueError("Too few samples to estimate a rolling window's size.")

        return step
