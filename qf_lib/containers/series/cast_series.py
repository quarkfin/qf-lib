
def cast_series(series, output_type):
    """
    Casts the given series to another series type specified by output_type (e.g. casts container of type pd.Series
    to QFSeries).

    Parameters
    ----------
    series: pd.Series
        series to be casted
    output_type: type
        type to which series should be casted

    Returns
    -------
    casted_series: pd.Series
        new series of given type
    """
    return output_type(data=series.values, index=series.index).__finalize__(series)
