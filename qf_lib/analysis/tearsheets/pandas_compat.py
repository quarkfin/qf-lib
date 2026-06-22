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


def _ticker_name(ticker):
    return getattr(ticker, "name", ticker)


def count_assets_by_name(positions_history: pd.DataFrame) -> pd.Series:
    """
    Count how many distinct asset names have an open position for each timestamp.
    """
    return positions_history.notna().T.groupby(_ticker_name).any().sum(axis=0)


def max_abs_exposure_by_name(positions_history: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-contract exposures into per-asset exposures using the max absolute value per timestamp.
    """
    return positions_history.abs().T.groupby(_ticker_name).max().T
