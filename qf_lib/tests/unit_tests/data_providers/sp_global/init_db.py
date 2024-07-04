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
from sqlalchemy import MetaData, Table, Column, VARCHAR, Numeric, DATE, Integer, Float, TIMESTAMP, CLOB


def initialize_database(engine):
    metadata = MetaData()

    Table('ciqcompany', metadata,
          Column('companyid', Integer, primary_key=True,
                 nullable=False),
          Column('companyname', VARCHAR(length=100)),
          Column('city', VARCHAR(length=100)),
          Column('companystatustypeid', Integer),
          Column('companytypeid', Integer),
          Column('officefaxvalue', VARCHAR(length=50)),
          Column('officephonevalue', VARCHAR(length=50)),
          Column('otherphonevalue', VARCHAR(length=50)),
          Column('simpleindustryid', Integer),
          Column('streetaddress', VARCHAR(length=200)),
          Column('streetaddress2', VARCHAR(length=200)),
          Column('streetaddress3', VARCHAR(length=200)),
          Column('streetaddress4', VARCHAR(length=200)),
          Column('yearfounded', Integer),
          Column('monthfounded', Integer),
          Column('dayfounded', Integer),
          Column('zipcode', VARCHAR(length=50)),
          Column('webpage', VARCHAR(length=500)),
          Column('reportingtemplatetypeid', Integer),
          Column('countryid', Integer),
          Column('stateid', Integer),
          Column('incorporationcountryid', Integer),
          Column('incorporationstateid', Integer))

    Table('ciqtradingitem', metadata,
          Column('tradingitemid', Integer, primary_key=True,
                 nullable=False),
          Column('securityid', Integer),
          Column('tickersymbol', VARCHAR(length=25)),
          Column('exchangeid', Integer),
          Column('currencyid', Integer),
          Column('tradingitemstatusid', Integer),
          Column('primaryflag', Numeric(precision=1, scale=0, asdecimal=False)))

    Table('ciqcurrency', metadata,
          Column('currencyid', Integer, primary_key=True,
                 nullable=False),
          Column('currencyname', VARCHAR(length=50)),
          Column('countryid', Integer),
          Column('majorcurrencyflag', Numeric(precision=1, scale=0, asdecimal=False)),
          Column('isocode', VARCHAR(length=10)))

    Table('ciqpriceequity', metadata,
          Column('tradingitemid', Integer, primary_key=True,
                 nullable=False), Column('pricingdate', DATE(), primary_key=True, nullable=False),
          Column('priceopen', Float),
          Column('pricehigh', Float),
          Column('pricelow', Float),
          Column('pricemid', Float),
          Column('priceclose', Float),
          Column('pricebid', Float),
          Column('priceask', Float),
          Column('volume', Float),
          Column('adjustmentfactor', Float),
          Column('vwap', Float),
          Column('pacvertofeedpop', Integer, nullable=False))

    Table('ciqsecurity', metadata,
          Column('securityid', Integer, primary_key=True, nullable=False),
          Column('companyid', Integer),
          Column('securityname', VARCHAR(length=500)),
          Column('securitystartdate', DATE()), Column('securityenddate', DATE()),
          Column('securitysubtypeid', Integer),
          Column('primaryflag', Numeric(precision=1, scale=0, asdecimal=False)))

    Table('ciqsimpleindustry', metadata,
          Column('simpleindustryid', Integer, primary_key=True, nullable=False),
          Column('simpleindustrydescription', VARCHAR(length=128)))

    Table('ciqpriceequitydivadjfactor', metadata,
          Column('tradingitemid', Integer, primary_key=True, nullable=False),
          Column('fromdate', TIMESTAMP(), primary_key=True, nullable=False),
          Column('todate', DATE()),
          Column('divadjfactor', Float),
          Column('pacvertofeedpop', Integer, nullable=False))

    Table('ciqdividend', metadata,
          Column('dividendid', Integer, primary_key=True, nullable=False),
          Column('exdate', DATE(), nullable=False),
          Column('paydate', DATE()),
          Column('recorddate', DATE()),
          Column('announceddate', DATE()),
          Column('divamount', Float),
          Column('tradingitemid', Integer),
          Column('exchangeid', Integer),
          Column('currencyid', Integer),
          Column('divfreqtypeid', Integer),
          Column('dividendtypeid', Integer),
          Column('supplementaltypeid', Integer),
          Column('netamount', Float),
          Column('grossamount', Float))

    Table('ciqexchangerate', metadata,
          Column('currencyid', Integer, primary_key=True, nullable=False),
          Column('pricedate', DATE(), primary_key=True, nullable=False),
          Column('snapid', Integer, primary_key=True, nullable=False),
          Column('priceclose', Float),
          Column('bestpricedate', DATE()),
          Column('latestsnapflag', Numeric(precision=1, scale=0, asdecimal=False)),
          Column('carryforwardflag', Numeric(precision=1, scale=0, asdecimal=False)))

    Table('ciqestimateperiod', metadata,
          Column('estimateperiodid', Integer, primary_key=True, nullable=False),
          Column('periodtypeid', Integer, primary_key=True, nullable=False),
          Column('companyid', Integer),
          Column('fiscalchainseriesid', Integer),
          Column('fiscalquarter', Integer),
          Column('fiscalyear', Integer),
          Column('calendarquarter', Integer),
          Column('calendaryear', Integer),
          Column('periodenddate', DATE()),
          Column('advancedate', DATE()))

    Table('ciqestimateconsensus', metadata,
          Column('estimateconsensusid', Integer, primary_key=True, nullable=False),
          Column('estimateperiodid', Integer),
          Column('tradingitemid', Integer),
          Column('accountingstandardid', Integer),
          Column('parentflag', Numeric(precision=1, scale=0, asdecimal=False)),
          Column('primaryparentconsolflag', Numeric(precision=1, scale=0, asdecimal=False)))

    Table('ciqestimatenumericdata', metadata,
          Column('estimateconsensusid', Integer, primary_key=True, nullable=False),
          Column('dataitemid', Integer, primary_key=True, nullable=False),
          Column('effectivedate', DATE(), primary_key=True, nullable=False),
          Column('todate', DATE()),
          Column('dataitemvalue', Float),
          Column('splitfactor', Float),
          Column('currencyid', Integer),
          Column('estimatescaleid', Integer),
          Column('pacvertofeedpop', Integer, nullable=False))

    Table('ciqmarketcap', metadata,
          Column('companyid', Integer, primary_key=True, nullable=False),
          Column('pricingdate', DATE(), primary_key=True, nullable=False),
          Column('marketcap', Float),
          Column('tev', Float),
          Column('sharesoutstanding', Integer))

    Table('ciqfinperiod', metadata, Column('financialperiodid', Integer, primary_key=True, nullable=False),
          Column('companyid', Integer), Column('periodtypeid', Numeric(precision=3, scale=0, asdecimal=False)),
          Column('calendaryear', Integer), Column('calendarquarter', Integer), Column('fiscalyear', Integer),
          Column('fiscalquarter', Integer),
          Column('latestperiodflag', Numeric(precision=1, scale=0, asdecimal=False), nullable=False),
          Column('fiscalchainseriesid', Integer))

    Table('ciqperiodtype', metadata,
          Column('periodtypeid', Numeric(precision=3, scale=0, asdecimal=False), primary_key=True, nullable=False),
          Column('periodtypename', VARCHAR(length=50)), Column('periodtypeabbreviation', VARCHAR(length=3)))

    Table('ciqfininstance', metadata, Column('financialinstanceid', Integer, primary_key=True, nullable=False),
          Column('financialperiodid', Integer), Column('periodenddate', DATE()), Column('filingdate', DATE()),
          Column('latestforfinancialperiodflag', Numeric(precision=1, scale=0, asdecimal=False)),
          Column('latestfilingforinstanceflag', Numeric(precision=1, scale=0, asdecimal=False)),
          Column('amendmentflag', Numeric(precision=1, scale=0, asdecimal=False)),
          Column('currencyid', Numeric(precision=5, scale=0, asdecimal=False)),
          Column('accessionnumber', VARCHAR(length=500)), Column('formtype', VARCHAR(length=100)),
          Column('restatementtypeid', Integer, nullable=False),
          Column('instancetypeid', Numeric(precision=3, scale=0, asdecimal=False)),
          Column('isrestatementtypeid', Numeric(precision=3, scale=0, asdecimal=False)),
          Column('bsrestatementtypeid', Numeric(precision=3, scale=0, asdecimal=False)),
          Column('cfrestatementtypeid', Numeric(precision=3, scale=0, asdecimal=False)), Column('documentid', Integer))

    Table('ciqfininstancetocollection', metadata,
          Column('financialinstanceid', Integer, primary_key=True, nullable=False),
          Column('financialcollectionid', Integer, primary_key=True, nullable=False),
          Column('instancetocollectiontypeid', Numeric(precision=3, scale=0, asdecimal=False)))

    Table('ciqfincollection', metadata, Column('financialcollectionid', Integer, primary_key=True, nullable=False),
          Column('financialinstanceid', Integer, nullable=False),
          Column('datacollectiontypeid', Numeric(precision=3, scale=0, asdecimal=False)), Column('nummonths', Integer),
          Column('currencyid', Numeric(precision=5, scale=0, asdecimal=False)),
          Column('nonstandardlengthflag', Numeric(precision=1, scale=0, asdecimal=False)))

    Table('ciqfincollectiondata', metadata,
          Column('financialcollectionid', Integer, primary_key=True, nullable=False),
          Column('dataitemid', Integer, primary_key=True, nullable=False),
          Column('dataitemvalue', Float), Column('unittypeid', Integer),
          Column('nmflag', Numeric(precision=1, scale=0, asdecimal=False)),
          Column('pacvertofeedpop', Integer, nullable=False))

    Table('ciqdataitem', metadata, Column('dataitemid', Integer, primary_key=True, nullable=False),
          Column('dataitemname', VARCHAR(length=200)),
          Column('dataitemdescription', CLOB()))

    Table('ciqiadividendchain', metadata, Column('tradingitemid', Integer, primary_key=True, nullable=False),
          Column('startdate', DATE(), primary_key=True, nullable=False), Column('enddate', DATE()),
          Column('dataitemvalue', Float),
          Column('dividendfrequency', Float), Column('companyid', Integer),
          Column('currencyid', Numeric(precision=5, scale=0, asdecimal=False)))

    # Create tables in the database
    metadata.create_all(engine)
