import pandas as pd

from qf_common.config.ioc import container
from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.document_exporting.element.table import Table
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider

pd.options.display.max_rows = 100000
pd.options.display.max_columns = 100


data_provider = container.resolve(QuandlDataProvider)  # type: QuandlDataProvider
start_date = str_to_date('2016-01-01')
end_date = str_to_date('2017-12-31')

# ================== Single series usage ========================

ticker = QuandlTicker('IBM', 'WIKI')
series = data_provider.get_price(tickers=ticker, fields=PriceField.Close, start_date=start_date, end_date=end_date)

ta = TimeseriesAnalysis(series, Frequency.DAILY)
print(TimeseriesAnalysis.values_in_table(ta))

# ================== DataFrame usage ========================

many_tickers = [QuandlTicker('MSFT', 'WIKI'), QuandlTicker('AAPL', 'WIKI'),
                QuandlTicker('EA', 'WIKI'), QuandlTicker('IBM', 'WIKI')]

df = data_provider.get_price(tickers=many_tickers, fields=PriceField.Close, start_date=start_date, end_date=end_date)
df.fillna(method='ffill', inplace=True)
print(TimeseriesAnalysis.table_for_df(df))

# ================== List of TA ========================
ta_list = [TimeseriesAnalysis(df[series_name], Frequency.DAILY) for series_name in df]

print(TimeseriesAnalysis.values_in_table(ta_list))

print(TimeseriesAnalysis.values_in_table(ta_list, df.columns))

# ================== PDF Table usage ========================

table = Table()
ta.populate_table(table)






