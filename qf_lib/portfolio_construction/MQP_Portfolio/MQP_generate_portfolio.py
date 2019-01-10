from qf_common.config import ioc
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.bloomberg import BloombergDataProvider

allocation_date = str_to_date('2018-11-29')
stressLevel = 1  # to be passed from stress level calculation'


# ===== get tickers, weights and units =====

data_provider = ioc.container.resolve(BloombergDataProvider)  # type: BloombergDataProvider
riy_ticker = BloombergTicker('RIY Index')
field = 'INDX_MEMBERS'

riy_ticker_names = data_provider.get_tabular_data(riy_ticker, field)

# (optionally) remove bought companies
tickers_to_remove = ['RHT ', 'DNB ', 'VVC ', 'FCE/A ', 'AET ']  # put a space after the ticker!
for name in riy_ticker_names:
    for name_to_remove in tickers_to_remove:
        if name_to_remove in name:
            riy_ticker_names.remove(name)
            tickers_to_remove.remove(name_to_remove)
            print("Ticker {} removed from list".format(name))
            break
if len(tickers_to_remove) > 0:
    print("Signatures {} were not found in the list of Tickers.".format(tickers_to_remove))

# create tickers
tickers_universe = []
for elem in riy_ticker_names:
    ticker_name = elem + " Equity"
    ticker = BloombergTicker(ticker_name)
    tickers_universe.append(ticker)
