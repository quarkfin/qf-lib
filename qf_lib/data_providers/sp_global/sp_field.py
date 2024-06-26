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
from enum import Enum


class SPField(Enum):

    # Market Data - Prices
    DivYield = 'divyield'
    BidPrice = 'pricebid'
    AskPrice = 'priceask'
    ClosePrice = 'priceclose'
    OpenPrice = 'priceopen'
    LowPrice = 'pricelow'
    HighPrice = 'pricehigh'
    Volume = 'volume'
    Currency = 'currency'

    BookValPerSH = '4020'
    EPS = '9'  # Earnings Per Share
    DvdPayOutRatio = '4377'
    Sales = '112'
    ROE = '4128'  # Return On Equity
    RetCap = '43905'
    ProfMargin = '4094'
    Total_Debt_to_Capital = '43907'
    GrossMargin = '4074'
    CurrentRatio = '4030'
    NetDebtToEBITDA = '4193'
    TotalAssetTurnover = '4177'
    EBITDA = '4051'  # Earnings Before Interest Taxes Depreciation and Amortization
    NetIncome = '15'


class SPDateType(Enum):
    periodenddate = 'periodenddate'
    filingdate = 'filingdate'
