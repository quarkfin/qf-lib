import numpy as np

from qf_lib.containers.dataframe.log_returns_dataframe import LogReturnsDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.point_emphasis_decorator import PointEmphasisDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def get_cone_chart(paths_data_frame, series_list, names_list, title=None, log_sacle=True):
    """
    Helper function to plot simulated paths together with significant lines (like expectation)
    """
    line_chart = LineChart(log_scale=log_sacle)

    # plot all paths
    for series_name in paths_data_frame:
        series_element = DataElementDecorator(paths_data_frame[series_name], linewidth=1)
        line_chart.add_decorator(series_element)

    legend_decorator = LegendDecorator(key='legend')
    colors = ['black', 'red', 'green', 'purple', 'lime']
    for i in range(len(series_list)):
        series = series_list[i]
        name = names_list[i]
        series_element = DataElementDecorator(series, color=colors[i % len(colors)], linewidth=3)
        line_chart.add_decorator(series_element)
        legend_decorator.add_entry(series_element, name)

        point = (series.index[-1], series[series.index[-1]])
        point_emphasis = PointEmphasisDecorator(series_element, point, move_point=False)
        line_chart.add_decorator(point_emphasis)

    line_chart.add_decorator(legend_decorator)

    # Create a title.
    if title is not None:
        title_decorator = TitleDecorator(title, "title")
        line_chart.add_decorator(title_decorator)

    return line_chart


def generate_random_paths(sample_len: int, sample_size: int, mean: float, std: float, leverage: float = 1.0):
    """ Generates random paths.

    Parameters
    ------------
    sample_len: int
        length of each path of data, equivalent to time
    sample_size: int
        Number of paths simulated
    mean: float
        mean simle return
    std: float
        standard deviation of returns
    leverage: float
        leverage used in the simulated investment process

    Returns
    -----------
    SimpleReturnsDataFrame
        indexed by steps with paths as columns
    """
    mean = mean * leverage
    std = std * leverage

    time = np.arange(1, 1 + sample_len)

    returns_vector = np.random.normal(loc=mean, scale=std, size=(sample_len * sample_size, 1))
    returns = np.reshape(returns_vector, (sample_len, sample_size))
    return SimpleReturnsDataFrame(data=returns, index=time)


def generate_random_log_paths(sample_len: int, sample_size: int, mean: float, std: float, leverage: float = 1.0):
    """
    Equivalent of generate_random_paths, but uses log Returns instead
    """
    mean = mean * leverage
    std = std * leverage

    # Setting the mean of log returns at m - 0.5σ^2 ensures that returns have mean m regardless of σ^2
    mean = mean - 0.5 * std * std

    time = np.arange(1, 1 + sample_len)

    returns_vector = np.random.normal(loc=mean, scale=std, size=(sample_len * sample_size, 1))
    returns = np.reshape(returns_vector, (sample_len, sample_size))
    return LogReturnsDataFrame(data=returns, index=time)
