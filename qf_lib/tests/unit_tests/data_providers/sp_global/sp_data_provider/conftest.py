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
from datetime import datetime, date

import pytest

from qf_lib.data_providers.sp_global.exchange_rates import SPExchangeRate
from qf_lib.data_providers.sp_global.sp_data_provider import SPDataProvider


@pytest.fixture
def fill_ciqcurrency(session, Base):
    ciqcurrency = Base.classes.ciqcurrency
    usd = ciqcurrency(currencyid=160, currencyname="US Dollar", countryid=213, majorcurrencyflag=1, isocode="USD")
    jpy = ciqcurrency(currencyid=79, currencyname="Japanese Yen", countryid=102, majorcurrencyflag=1, isocode="JPY")
    session.add(usd)
    session.add(jpy)

    session.commit()


@pytest.fixture
def fill_ciqexchangerate(session, Base):
    ciqexchangerate = Base.classes.ciqexchangerate
    prices_usd = [
        ciqexchangerate(currencyid=160, pricedate=datetime(2011, 1, 1), priceclose=1, snapid=6),
        ciqexchangerate(currencyid=160, pricedate=datetime(2011, 1, 2), priceclose=1, snapid=6),
        ciqexchangerate(currencyid=160, pricedate=datetime(2011, 1, 3), priceclose=1, snapid=6),
        ciqexchangerate(currencyid=160, pricedate=datetime(2011, 1, 4), priceclose=1, snapid=6),
        ciqexchangerate(currencyid=160, pricedate=datetime(2011, 1, 5), priceclose=1, snapid=6)
    ]
    prices_jpy = [
        ciqexchangerate(currencyid=79, pricedate=datetime(2011, 1, 1), priceclose=150.0, snapid=6),
        ciqexchangerate(currencyid=79, pricedate=datetime(2011, 1, 2), priceclose=151.0, snapid=6),
        ciqexchangerate(currencyid=79, pricedate=datetime(2011, 1, 3), priceclose=152.0, snapid=6),
        ciqexchangerate(currencyid=79, pricedate=datetime(2011, 1, 4), priceclose=153.0, snapid=6),
        ciqexchangerate(currencyid=79, pricedate=datetime(2011, 1, 5), priceclose=152.0, snapid=6)
    ]

    session.bulk_save_objects(prices_usd)
    session.bulk_save_objects(prices_jpy)

    session.commit()


@pytest.fixture
def fill_ciqtradingitem(session, Base):
    ciqtradingitem = Base.classes.ciqtradingitem

    session.add(ciqtradingitem(tradingitemid=2001, currencyid=79))
    session.add(ciqtradingitem(tradingitemid=2002, currencyid=None))
    session.add(ciqtradingitem(tradingitemid=2008, currencyid=160))

    usd_tickers = [ciqtradingitem(tradingitemid=tid, currencyid=160) for tid in range(2003, 2007)]
    session.bulk_save_objects(usd_tickers)

    session.commit()


@pytest.fixture
def fill_ciqpriceequity(session, Base):
    ciqpriceequity = Base.classes.ciqpriceequity

    # Add pricing data for a trading item id, which does not have a corresponding currency id
    for tid in range(2001, 2008):
        prices = [
            ciqpriceequity(tradingitemid=tid, pricingdate=date(2011, 1, 1), priceclose=20.0, volume=100.0,
                           pacvertofeedpop=561),
            ciqpriceequity(tradingitemid=tid, pricingdate=date(2011, 1, 2), priceclose=21.0,
                           pacvertofeedpop=561),
            ciqpriceequity(tradingitemid=tid, pricingdate=date(2011, 1, 4), priceclose=22.0, volume=300.0,
                           pacvertofeedpop=561),
            ciqpriceequity(tradingitemid=tid, pricingdate=date(2011, 1, 5), priceclose=23.0, volume=400.0,
                           pacvertofeedpop=561)
        ]

        session.bulk_save_objects(prices)

    session.commit()


@pytest.fixture
def fill_ciqiadividendchain(session, Base):
    ciqiadividendchain = Base.classes.ciqiadividendchain

    # Dividends with currency (USD)
    dividends_2003 = [
        ciqiadividendchain(tradingitemid=2003, startdate=date(2011, 1, 4), enddate=None, dataitemvalue=50,
                           currencyid=160),
        ciqiadividendchain(tradingitemid=2003, startdate=date(2001, 1, 4), enddate=date(2011, 1, 4), dataitemvalue=10,
                           currencyid=160)
    ]

    # Dividends with currency (USD)
    dividends_2001 = [
        ciqiadividendchain(tradingitemid=2001, startdate=date(2011, 1, 4), enddate=None, dataitemvalue=50,
                           currencyid=160),
        ciqiadividendchain(tradingitemid=2001, startdate=date(2001, 1, 4), enddate=date(2011, 1, 4), dataitemvalue=10,
                           currencyid=160)
    ]

    # Dividends with currency (JPY)
    dividends_2004 = [
        ciqiadividendchain(tradingitemid=2004, startdate=date(2011, 1, 4), enddate=None, dataitemvalue=50,
                           currencyid=79),
        ciqiadividendchain(tradingitemid=2004, startdate=date(2001, 1, 4), enddate=date(2011, 1, 4), dataitemvalue=10,
                           currencyid=79)
    ]

    # Dividends with a gap
    dividends_2005 = [
        ciqiadividendchain(tradingitemid=2005, startdate=date(2011, 1, 4), enddate=None, dataitemvalue=50,
                           currencyid=79),
        ciqiadividendchain(tradingitemid=2005, startdate=date(2001, 1, 4), enddate=date(2011, 1, 1), dataitemvalue=10,
                           currencyid=79)
    ]

    # Dividends with mixed currencies
    dividends_2006 = [
        ciqiadividendchain(tradingitemid=2006, startdate=date(2011, 1, 4), enddate=None, dataitemvalue=50,
                           currencyid=79),
        ciqiadividendchain(tradingitemid=2006, startdate=date(2001, 1, 4), enddate=date(2011, 1, 4), dataitemvalue=10,
                           currencyid=160)
    ]

    session.bulk_save_objects(dividends_2001)
    session.bulk_save_objects(dividends_2003)
    session.bulk_save_objects(dividends_2004)
    session.bulk_save_objects(dividends_2005)
    session.bulk_save_objects(dividends_2006)

    session.commit()


@pytest.fixture
def fill_dummy_data(fill_ciqcurrency, fill_ciqtradingitem, fill_ciqpriceequity, fill_ciqexchangerate,
                    fill_ciqiadividendchain):
    yield


@pytest.fixture
def sp_data_provider(db_conn_provider, fill_dummy_data):
    return SPDataProvider(db_conn_provider, True, SPExchangeRate.LondonClose)
