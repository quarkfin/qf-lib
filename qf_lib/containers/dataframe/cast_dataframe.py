from pandas import DataFrame


def cast_dataframe(dataframe: DataFrame, output_type: type):
    """
    Casts the given dataframe to another dataframe type specified by output_type (e.g. casts container of type
    pd.DataFrame to QFDataFrame).

    Parameters
    ----------
    dataframe
        dataframe to be casted
    output_type
        type to which dataframe should be casted

    Returns
    -------
    casted_dataframe
        new dataframe of given type
    """
    return output_type(data=dataframe.values, index=dataframe.index, columns=dataframe.columns).__finalize__(dataframe)
