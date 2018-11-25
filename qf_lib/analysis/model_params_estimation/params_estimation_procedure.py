

all_tickers = []  # all tickers to begin with

# repeat in the loop for every step of the process:
for is_start, is_end, oos_start, oos_end in steps:


    # tickers that achieved in any parameter set  SQN of at least 0.4 while trading more that 10 times a year.
    selected_tickers = get_selected_tickers(all_tickers)

    # calculates the structures containing quality of the trading model (SQN) for all selected tickers combined and for
    # individual tickers. The structure will be later presented as a collection of heat maps or charts
    trading_summary = calculate_trading_summary(selected_tickers)

    # smoothes the matrix using filter and selects the best parameters
    selected_parameters = selecte_best_parameters(trading_summary)

    # save selected parameters together with the time range in which they should be traded.
    result.append((oos_start, oos_end, selected_tickers))



def get_selected_tickers(all_tickers):
    pass
