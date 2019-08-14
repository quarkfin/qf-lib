#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import pandas as pd

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.documents_utils.document_exporting.element.table import Table
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider

start_date = str_to_date('2016-01-01')
end_date = str_to_date('2017-12-31')

pd.options.display.max_rows = 100000
pd.options.display.max_columns = 100

ticker = QuandlTicker('IBM', 'WIKI')
many_tickers = [
    QuandlTicker('MSFT', 'WIKI'),
    QuandlTicker('AAPL', 'WIKI'),
    QuandlTicker('EA', 'WIKI'),
    QuandlTicker('IBM', 'WIKI')]


def _single_series_usage(data_provider):
    series = data_provider.get_price(tickers=ticker, fields=PriceField.Close, start_date=start_date, end_date=end_date)
    ta = TimeseriesAnalysis(series, Frequency.DAILY)
    print(TimeseriesAnalysis.values_in_table(ta))
    return ta


def _dataframe_usage(data_provider):
    df = data_provider.get_price(
        tickers=many_tickers, fields=PriceField.Close, start_date=start_date, end_date=end_date)
    df.fillna(method='ffill', inplace=True)
    print(TimeseriesAnalysis.table_for_df(df))
    return df


def _list_of_ta(df):
    ta_list = [TimeseriesAnalysis(df[series_name], Frequency.DAILY) for series_name in df]
    print(TimeseriesAnalysis.values_in_table(ta_list))
    print(TimeseriesAnalysis.values_in_table(ta_list, df.columns))


def _pdf_usage(ta):
    table = Table()
    ta.populate_table(table)


def main():
    data_provider = container.resolve(QuandlDataProvider)  # type: QuandlDataProvider

    ta = _single_series_usage(data_provider)
    df = _dataframe_usage(data_provider)

    _list_of_ta(df)
    _pdf_usage(ta)


if __name__ == '__main__':
    main()
