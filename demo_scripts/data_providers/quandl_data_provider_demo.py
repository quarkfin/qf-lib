import pandas as pd

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.quandl_db_type import QuandlDBType
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider

pd.options.display.max_rows = 100000
pd.options.display.max_columns = 100


def main():
    data_provider = container.resolve(QuandlDataProvider)  # type: QuandlDataProvider
    start_date = str_to_date('2016-01-01')
    end_date = str_to_date('2017-11-02')

    print('Single ticker:')
    ticker = QuandlTicker('IBM', 'WIKI')
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Single ticker: lower case')
    ticker = QuandlTicker('ibm', 'wiki')
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Single ticker:')
    ticker = QuandlTicker('IBM', 'WIKI/PRICES', QuandlDBType.Table)
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Single ticker, Price')
    ticker = QuandlTicker('IBM', 'WIKI/PRICES', QuandlDBType.Table)
    data = data_provider.get_price(tickers=ticker, fields=PriceField.Close, start_date=start_date, end_date=end_date)
    print(data)

    print('Continues Futures - CHRIS')
    ticker = QuandlTicker('ASX_TN2', 'CHRIS')
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Futures - ICE')
    ticker = QuandlTicker('OZ2019', 'ICE')
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Futures - CME')
    ticker = QuandlTicker('EMF2018', 'CME')
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Futures - EUREX')
    ticker = QuandlTicker('FCXEZ2018', 'EUREX')
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Continues Futures - CHRIS')
    ticker = QuandlTicker('ASX_TN2', 'CHRIS')
    data = data_provider.get_price(tickers=ticker, fields=PriceField.Close, start_date=start_date, end_date=end_date)
    print(data)


if __name__ == '__main__':
    main()
