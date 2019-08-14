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


class TradeField(Enum):
    """
    Represents data fields that are properties of the Trade.
    """

    Ticker = 0
    """
    The Ticker which was traded in the Trade.
    """

    StartDate = 1
    """
    Date when the Trade was entered.
    """

    EndDate = 2
    """
    Date when the Trade was closed.
    """

    Open = 3
    """
    Price at which the Trade was entered (opened).
    """

    MaxGain = 4
    """
    Maximum difference between the value of the Trade and the price at which the Trade was entered.
    Can be 0.0 if the Trade was only loosing a value. Expressed in currency units (e.g. 1200.0).
    """

    MaxLoss = 5
    """
    Maximum negative difference between the value of the Trade and the price at which the Trade was entered.
    It's always negative. Can be 0.0 if the Trade was only gaining a value. Expressed in currency units (e.g. -100.0).
    """

    Close = 6
    """
    Price at which the Trade was exited (closed).
    """

    Return = 7
    """
    Arithmetic return on the Trade (Close/Open - 1 for the Long Trade and 1 - Close/Open for the Short Trade).
    """

    Exposure = 8
    """
    1.0 for the Long Trade and -1.0 for the Short Trade.
    """
