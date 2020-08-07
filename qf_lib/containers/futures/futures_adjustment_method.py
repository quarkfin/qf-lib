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


class FuturesAdjustmentMethod(Enum):
    """
    Method used to join the prices of different future contracts, belonging to one future chain.
    """
    NTH_NEAREST = 0,
    """NTH_NEAREST - the price data for a certain period of time is taken from the N-th contract, there is no
    discontinuities correction at the contract expiry dates"""
    BACK_ADJUSTED = 1
    """BACK_ADJUST - the historical price discontinuities are corrected, so that they would align smoothly on the expiry
    date. The gaps between consecutive contracts are being adjusted, by shifting the historical data by the difference
    between the Open price on the first day of new contract and Close price on the last day of the old contract.
    The back adjustment considers only the Open, High, Low, Close price values. The Volumes are not being adjusted."""
