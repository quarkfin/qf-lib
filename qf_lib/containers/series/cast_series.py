from pandas import Series


def cast_series(series: Series, output_type: type):
    """
    Casts the given series to another series type specified by output_type (e.g. casts container of type pd.Series
    to QFSeries).

    Parameters
    ----------
    series
        series to be casted
    output_type
        type to which series should be casted

    Returns
    -------
    casted_series
        new series of given type
    """
    return output_type(data=series.values, index=series.index).__finalize__(series)
