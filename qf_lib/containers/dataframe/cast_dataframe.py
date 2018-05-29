
def cast_dataframe(dataframe, output_type):
    """
    Casts the given dataframe to another dataframe type specified by output_type (e.g. casts container of type
    pd.DataFrame to QFDataFrame).

    Parameters
    ----------
    dataframe: pd.DataFrame
        dataframe to be casted
    output_type: type
        type to which dataframe should be casted

    Returns
    -------
    casted_dataframe: pd.DataFrame
        new dataframe of given type
    """
    return output_type(data=dataframe.values, index=dataframe.index, columns=dataframe.columns).__finalize__(dataframe)
