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

import pytest
from numpy import nan
from pandas import DatetimeIndex, notna, isna
from pandas._testing import assert_frame_equal, assert_series_equal

from qf_lib.common.tickers.tickers import SPTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.sp_global.sp_field import SPField


def test_adjustment__volume(sp_data_provider, session, Base):
    """
    Test volume series output. Trading item id has corporate actions within the time range, but they should not affect
    volume.
    """
    ciqdividend = Base.classes.ciqdividend
    ciqpriceequitydivadjfactor = Base.classes.ciqpriceequitydivadjfactor

    corporate_actions_and_adjustment_2002 = [
        ciqdividend(dividendid=1, exdate=datetime(2011, 1, 2), tradingitemid=2002, dividendtypeid=20),
        ciqdividend(dividendid=2, exdate=datetime(2018, 1, 2), tradingitemid=2002, dividendtypeid=20),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 4), todate=None,
                                   divadjfactor=1, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 2), todate=datetime(2011, 1, 3),
                                   divadjfactor=0.95, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2010, 1, 2), todate=datetime(2011, 1, 1),
                                   divadjfactor=0.85, pacvertofeedpop=561),
    ]

    session.bulk_save_objects(corporate_actions_and_adjustment_2002)
    session.commit()

    volumes = sp_data_provider.get_history(SPTicker(2002), SPField.Volume, datetime(2011, 1, 1), datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-04', '2011-01-05'], name="dates")
    expected_volume = QFSeries([100.0, 300.0, 400.0], index, name="2002")
    assert_series_equal(volumes, expected_volume)


def test_adjustment__single_ticker_single_field_1(sp_data_provider, session, Base):
    """
    Test adjustment of pricing data.
    - There is no corporate action before the start datetime
    - There is no corporate action between start and end datetime
    - There are multiple corporate actions after the end datetime
    The adjustment is always applied as of end datetime. If a corporate action occurred afterwards, it is not taken
    into account when computing prices adjustment.
    """
    ciqdividend = Base.classes.ciqdividend
    ciqpriceequitydivadjfactor = Base.classes.ciqpriceequitydivadjfactor

    # Add corporate actions for 2001
    corporate_actions_and_adjustment_2001 = [
        ciqdividend(dividendid=1, exdate=datetime(2012, 1, 6), tradingitemid=2001, dividendtypeid=20),
        ciqdividend(dividendid=2, exdate=datetime(2018, 1, 10), tradingitemid=2001, dividendtypeid=20),
        ciqpriceequitydivadjfactor(tradingitemid=2001, fromdate=datetime(2018, 1, 10), todate=None,
                                   divadjfactor=1, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2001, fromdate=datetime(2011, 1, 6), todate=datetime(2018, 1, 9),
                                   divadjfactor=0.75, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2001, fromdate=datetime(2010, 1, 2), todate=datetime(2011, 1, 5),
                                   divadjfactor=0.6, pacvertofeedpop=561),
    ]
    session.bulk_save_objects(corporate_actions_and_adjustment_2001)
    session.commit()

    prices = sp_data_provider.get_history(SPTicker(2001), SPField.ClosePrice, datetime(2011, 1, 1),
                                          datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_prices = QFSeries([20.0, 21.0, 22.0, 23.0], index, name="2001")
    assert_series_equal(prices, expected_prices)


def test_adjustment__single_ticker_single_field_2(sp_data_provider, session, Base):
    """
    Test adjustment of pricing data. The close price should be adjusted only if adjustment = True.
    - There is no corporate action before the start datetime
    - There is a single corporate action between start and end datetime
    - There is no corporate action after the end datetime
    Adjustment ratio is equal to the divadjfactor change between 2011-01-01 and 2011-01-02
    """
    ciqdividend = Base.classes.ciqdividend
    ciqpriceequitydivadjfactor = Base.classes.ciqpriceequitydivadjfactor

    corporate_actions_and_adjustment_2002 = [
        ciqdividend(dividendid=1, exdate=datetime(2011, 1, 2), tradingitemid=2002, dividendtypeid=20),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 4), todate=None,
                                   divadjfactor=1, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 2), todate=datetime(2011, 1, 3),
                                   divadjfactor=0.95, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2010, 1, 2), todate=datetime(2011, 1, 1),
                                   divadjfactor=0.85, pacvertofeedpop=561),
    ]

    session.bulk_save_objects(corporate_actions_and_adjustment_2002)
    session.commit()

    ratio = 0.95 / 0.85
    prices = sp_data_provider.get_history(SPTicker(2002), SPField.ClosePrice, datetime(2011, 1, 1),
                                          datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_prices = QFSeries([15.0 / ratio, 16.0, 17.0, 18.0], index, name="2002")
    assert_series_equal(prices, expected_prices)


def test_adjustment__single_ticker_single_field_3(sp_data_provider, session, Base):
    """
    Test adjustment of pricing data. The close price should be adjusted only if adjustment = True.
    - There is a corporate action before the start_datetime
    - There is only a single corporate action between start and end datetime
    - There are multiple corporate actions after the end datetime
    Adjustment ratio is equal to the divadjfactor change between 2011-01-01 and 2011-01-02
    """
    ciqdividend = Base.classes.ciqdividend
    ciqpriceequitydivadjfactor = Base.classes.ciqpriceequitydivadjfactor

    corporate_actions_and_adjustment_2002 = [
        ciqdividend(dividendid=1, exdate=datetime(2011, 1, 2), tradingitemid=2002, dividendtypeid=20),
        ciqdividend(dividendid=2, exdate=datetime(2011, 1, 9), tradingitemid=2002, dividendtypeid=20),
        ciqdividend(dividendid=3, exdate=datetime(2018, 1, 2), tradingitemid=2002, dividendtypeid=20),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2018, 1, 2), todate=None,
                                   divadjfactor=1, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 9), todate=datetime(2018, 1, 1),
                                   divadjfactor=0.97, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 4), todate=datetime(2011, 1, 8),
                                   divadjfactor=0.95, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 2), todate=datetime(2011, 1, 3),
                                   divadjfactor=0.90, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2010, 1, 2), todate=datetime(2011, 1, 1),
                                   divadjfactor=0.85, pacvertofeedpop=561),
    ]

    session.bulk_save_objects(corporate_actions_and_adjustment_2002)
    session.commit()

    ratio = 0.90 / 0.85
    prices = sp_data_provider.get_history(SPTicker(2002), SPField.ClosePrice, datetime(2011, 1, 1),
                                          datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_prices = QFSeries([15.0 / ratio, 16.0, 17.0, 18.0], index, name="2002")
    assert_series_equal(prices, expected_prices)


def test_adjustment__single_ticker_single_field_4(sp_data_provider, session, Base):
    """
    Test adjustment of pricing data. The close price should be adjusted only if adjustment = True.
    - There is a corporate action before the start_datetime
    - There are multiple corporate actions between start and end datetime
    - There are multiple corporate actions after the end datetime
    Adjustment ratio is equal to the divadjfactor change between 2011-01-01 and 2011-01-02
    """
    ciqdividend = Base.classes.ciqdividend
    ciqpriceequitydivadjfactor = Base.classes.ciqpriceequitydivadjfactor

    corporate_actions_and_adjustment_2002 = [
        ciqdividend(dividendid=1, exdate=datetime(2011, 1, 2), tradingitemid=2002, dividendtypeid=20),
        ciqdividend(dividendid=2, exdate=datetime(2011, 1, 4), tradingitemid=2002, dividendtypeid=20),
        ciqdividend(dividendid=3, exdate=datetime(2011, 1, 9), tradingitemid=2002, dividendtypeid=20),
        ciqdividend(dividendid=4, exdate=datetime(2018, 1, 2), tradingitemid=2002, dividendtypeid=20),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2018, 1, 2), todate=None,
                                   divadjfactor=1, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 9), todate=datetime(2018, 1, 1),
                                   divadjfactor=0.97, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 4), todate=datetime(2011, 1, 8),
                                   divadjfactor=0.95, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2011, 1, 2), todate=datetime(2011, 1, 3),
                                   divadjfactor=0.90, pacvertofeedpop=561),
        ciqpriceequitydivadjfactor(tradingitemid=2002, fromdate=datetime(2010, 1, 2), todate=datetime(2011, 1, 1),
                                   divadjfactor=0.85, pacvertofeedpop=561),
    ]

    session.bulk_save_objects(corporate_actions_and_adjustment_2002)
    session.commit()

    ratio1 = 0.90 / 0.85
    ratio2 = 0.95 / 0.90
    prices = sp_data_provider.get_history(SPTicker(2002), SPField.ClosePrice, datetime(2011, 1, 1),
                                          datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_prices = QFSeries([15.0 / ratio1, 16.0 / (ratio1 * ratio2), 17.0, 18.0], index, name="2002")
    assert_series_equal(prices, expected_prices)
