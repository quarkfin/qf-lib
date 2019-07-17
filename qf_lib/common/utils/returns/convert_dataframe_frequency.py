from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame


def convert_dataframe_frequency(dataframe: QFDataFrame, frequency: Frequency) -> SimpleReturnsDataFrame:
    """
    Converts each column in the dataframe to the specified frequency.
    ValueError is raised when a column has a lower frequency than the one we are converting to.
    """
    # Verify that all columns in the dataframe have a lower frequency.
    data_frequencies = dataframe.get_frequency()
    for column, col_frequency in data_frequencies.items():
        if col_frequency < frequency:
            raise ValueError("Column '{}' cannot be converted to '{}' frequency because its frequency is '{}'.".format(
                column, frequency, col_frequency))

    if frequency == Frequency.DAILY:
        return dataframe.to_simple_returns()

    filled_df = dataframe.to_prices().fillna(method="ffill")
    new_columns = {}
    for column in filled_df:
        new_columns[column] = get_aggregate_returns(filled_df[column], frequency)

    return SimpleReturnsDataFrame(new_columns)
