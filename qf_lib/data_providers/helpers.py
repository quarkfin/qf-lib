def squeeze_panel(original_data_panel, got_single_date, got_single_ticker, got_single_field):
    original_shape = original_data_panel.shape

    # slice(None) corresponds to ':' in iloc[:] notation
    dates_indices = 0 if got_single_date else slice(None)
    tickers_indices = 0 if got_single_ticker else slice(None)
    fields_indices = 0 if got_single_field else slice(None)

    container = original_data_panel.iloc[dates_indices, tickers_indices, fields_indices]

    # correction of containers axis order (if last or pre-last axis is being removed, than the data frame needs
    # to be transposed to keep the axis order: dates, tickers, fields)
    if len(container.shape) == 2 and (original_shape[1] == 1 or original_shape[2] == 1):
        container = container.transpose()

    # if single ticker was provided, name the series or data frame by the ticker
    if original_shape[1] == 1 and original_shape[2] == 1:
        container.name = original_data_panel.major_axis[0].as_string()

    return container
