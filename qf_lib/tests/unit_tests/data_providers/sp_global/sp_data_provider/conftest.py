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
from datetime import datetime

import numpy as np
import pytest

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
    rng = np.random.default_rng(0)

    session.bulk_save_objects(
        [ciqtradingitem(tradingitemid=n, currencyid=rng.choice([79, 160, None])) for n in range(1, 1501)])

    session.add(ciqtradingitem(tradingitemid=2001, currencyid=79))
    session.add(ciqtradingitem(tradingitemid=2002, currencyid=None))
    session.add(ciqtradingitem(tradingitemid=2003, currencyid=160))
    session.add(ciqtradingitem(tradingitemid=3000, currencyid=160))

    session.commit()


@pytest.fixture
def fill_ciqpriceequity(session, Base):
    ciqpriceequity = Base.classes.ciqpriceequity

    # Add pricing data for a trading item id, which does not have a corresponding currency id and no corporate actions
    prices_tid_2002 = [
        ciqpriceequity(tradingitemid=2002, pricingdate=datetime(2011, 1, 1), priceclose=15.0, pricebid=14.5,
                       volume=100, pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2002, pricingdate=datetime(2011, 1, 2), priceclose=16.0, pricebid=15.5,
                       pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2002, pricingdate=datetime(2011, 1, 4), priceclose=17.0, pricebid=None,
                       volume=300, pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2002, pricingdate=datetime(2011, 1, 5), priceclose=18.0, pricebid=17.5,
                       volume=400, pacvertofeedpop=561)
    ]

    # Add pricing data for a trading item id, with currency = USD, with no corresponding corporate actions
    prices_tid_2003 = [
        ciqpriceequity(tradingitemid=2003, pricingdate=datetime(2011, 1, 1), priceclose=20.0,
                       volume=100, pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2003, pricingdate=datetime(2011, 1, 2), priceclose=21.0,
                       pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2003, pricingdate=datetime(2011, 1, 4), priceclose=22.0,
                       volume=300, pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2003, pricingdate=datetime(2011, 1, 5), priceclose=23.0,
                       volume=400, pacvertofeedpop=561)
    ]

    # Add pricing data for a trading item id, with currency = JPY, with no corresponding corporate actions
    prices_tid_2001 = [
        ciqpriceequity(tradingitemid=2001, pricingdate=datetime(2011, 1, 1), priceclose=20.0,
                       volume=100, pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2001, pricingdate=datetime(2011, 1, 2), priceclose=21.0,
                       pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2001, pricingdate=datetime(2011, 1, 4), priceclose=22.0,
                       volume=300, pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=2001, pricingdate=datetime(2011, 1, 5), priceclose=23.0,
                       volume=400, pacvertofeedpop=561)
    ]

    # Add pricing data for a trading item id, with currency = USD, with corresponding corporate actions
    prices_tid_3000 = [
        ciqpriceequity(tradingitemid=3000, pricingdate=datetime(2011, 1, 1), priceclose=20.0,
                       volume=100, pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=3000, pricingdate=datetime(2011, 1, 2), priceclose=21.0,
                       pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=3000, pricingdate=datetime(2011, 1, 4), priceclose=22.0,
                       volume=300, pacvertofeedpop=561),
        ciqpriceequity(tradingitemid=3000, pricingdate=datetime(2011, 1, 5), priceclose=23.0,
                       volume=400, pacvertofeedpop=561)
    ]

    session.bulk_save_objects(prices_tid_2002)
    session.bulk_save_objects(prices_tid_2003)
    session.bulk_save_objects(prices_tid_2001)
    session.bulk_save_objects(prices_tid_3000)

    session.commit()


@pytest.fixture
def fill_dummy_data(fill_ciqcurrency, fill_ciqtradingitem, fill_ciqpriceequity, fill_ciqexchangerate):
    yield


@pytest.fixture
def sp_data_provider(db_conn_provider, fill_dummy_data):
    return SPDataProvider(db_conn_provider, True, 6)
