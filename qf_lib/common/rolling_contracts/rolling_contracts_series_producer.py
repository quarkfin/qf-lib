from typing import Sequence, Dict

import numpy as np
import pandas as pd

from qf_lib.common.rolling_contracts.rolling_contracts_data import RollingContractData
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.returns_series import ReturnsSeries


class RollingContractsSeriesProducer(object):
    """
    Class producing a series (e.g. UX1) by rolling real contracts (e.g. UXJ07, UXK07, UXM07).
    """

    def __init__(self, timer: Timer):
        self.timer = timer
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_rolling_contracts_data(self, real_contracts_prices_df: PricesDataFrame, rolling_dates: pd.DatetimeIndex,
                                   contract_numbers: Sequence[int] = (1,)) \
            -> Dict[int, RollingContractData]:
        """
        Takes DataFrame of real contracts and creates a dictionary mapping contracts number to RollingContractData.

        Parameters
        ----------
        real_contracts_prices_df
            dataframe with prices of real contracts (e.g. UXZ06, UXF07 and UXG07)
        rolling_dates
            dates on which the rolling contract should be rolled
        contract_numbers
            list of integers. Example: for getting UX1 and UX2 it would be equal to (1, 2)

        Returns
        -------
        data for rolling contracts
        """
        rolling_dates = self._remove_future_rolling_dates(rolling_dates)

        real_contracts_prices_df = self._remove_unnecessary_data(real_contracts_prices_df, rolling_dates)
        contracts_data_dict = dict()

        for contract_number in contract_numbers:
            contract_data = self._get_single_rolling_contract_info(
                real_contracts_prices_df, rolling_dates, contract_number)
            contracts_data_dict[contract_number] = contract_data

        return contracts_data_dict

    def _remove_future_rolling_dates(self, rolling_dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
        """
        Checks if rolling_dates contain any dates from the future and if so, removes them from the list
        and returns the filtered list.
        """
        nonfuture_rolling_dates = rolling_dates[rolling_dates <= self.timer.now()]
        if len(nonfuture_rolling_dates) < len(rolling_dates):
            self.logger.warning("rolling_dates contains future dates")

        return nonfuture_rolling_dates

    def _remove_unnecessary_data(self, real_contracts_prices_df: PricesDataFrame, rolling_dates: pd.DatetimeIndex) \
            -> PricesDataFrame:
        """
        Removes data which isn't necessary for calculating the rolling series from real contracts dataframe
        and returns the dataframe without unnecessary data.
        """
        real_contracts_prices_df = real_contracts_prices_df.loc[rolling_dates[0]:rolling_dates[-1], :]
        real_contracts_prices_df = real_contracts_prices_df.dropna(how='all', axis=1)

        return real_contracts_prices_df

    def _get_single_rolling_contract_info(self, real_contracts_prices_df: PricesDataFrame,
                                          rolling_dates: pd.DatetimeIndex, contract_number: int) \
            -> RollingContractData:
        now = self.timer.now()

        # lists of series (each series being a partial result, they are concatenated in the end)
        prices_tms_list = []
        returns_tms_list = []
        time_to_expiration_tms_list = []

        last_rolling_date_idx = len(rolling_dates) - 1
        for i, start_date in enumerate(rolling_dates):
            if i < last_rolling_date_idx:
                end_date = rolling_dates[i + 1]
            else:
                end_date = now

            front_contract_idx = contract_number - 1 + i
            front_contract_tms = real_contracts_prices_df.iloc[:, front_contract_idx]
            front_contract_tms = front_contract_tms.dropna()

            partial_prices_tms, partial_tte_tms = self._filter_tms(front_contract_tms, start_date, end_date)
            partial_returns_tms = partial_prices_tms.to_simple_returns()

            # remove price and first time to expiration for every contract except for the first one. Otherwise there
            # would be two data points on rolling dates
            # TODO think if the following code shouldn't be removed,
            # so that there would be 2 data points on rolling dates
            if i > 0:
                partial_prices_tms = partial_prices_tms.iloc[1:]
                partial_tte_tms = partial_tte_tms.iloc[1:]

            prices_tms_list.append(partial_prices_tms)
            time_to_expiration_tms_list.append(partial_tte_tms)
            returns_tms_list.append(partial_returns_tms)

        prices_tms = pd.concat(prices_tms_list, axis=0)
        prices_tms = cast_series(prices_tms, PricesSeries)
        time_to_expiration_tms = pd.concat(time_to_expiration_tms_list, axis=0)  # type: pd.Series
        returns_tms = pd.concat(returns_tms_list, axis=0)
        returns_tms = cast_series(returns_tms, ReturnsSeries)

        # set names for series
        self._set_series_names(contract_number, prices_tms, returns_tms, time_to_expiration_tms)

        return RollingContractData(prices_tms, time_to_expiration_tms, returns_tms)

    def _filter_tms(self, real_contracts_prices_tms, start_date, end_date):
        self._check_if_no_missing_data(start_date, end_date, real_contracts_prices_tms)

        last_trade_date = real_contracts_prices_tms.index[-1]

        # if rolling is not possible on a given rolling_date, then it is done at first possible date
        # the following code finds an index of first date greater or equal start date and first date greater or equal
        # end date
        start_date_idx = np.searchsorted(real_contracts_prices_tms.index, start_date)
        end_date_idx = np.searchsorted(real_contracts_prices_tms.index, end_date)

        filtered_prices_tms = real_contracts_prices_tms.iloc[start_date_idx:(end_date_idx + 1)]
        time_to_expiration_values = last_trade_date - filtered_prices_tms.index
        time_to_expiration_tms = pd.Series(data=time_to_expiration_values, index=filtered_prices_tms.index.copy())

        return filtered_prices_tms, time_to_expiration_tms

    def _set_series_names(self, contract_number, prices_tms, returns_tms, time_to_expiration_tms):
        contract_name = "contract_no_{:d}".format(contract_number)
        prices_tms.name = contract_name
        time_to_expiration_tms.name = contract_name
        returns_tms.name = contract_name

    def _check_if_no_missing_data(self, start_date, end_date, real_contracts_prices_tms):
        dates = real_contracts_prices_tms.index
        first_available_date = dates[0]
        last_available_date = dates[-1]

        if start_date < first_available_date or end_date > last_available_date:
            warning_msg = "Missing data for a period [{start_date:s},{end_date:s}]. Data available only " \
                          "for a period [{first_available_date:s},{last_available_date:s}] " \
                          "Contract name: {contract_name:s}".format(
                           start_date=date_to_str(start_date), end_date=date_to_str(end_date),
                           first_available_date=date_to_str(first_available_date),
                           last_available_date=date_to_str(last_available_date),
                           contract_name=real_contracts_prices_tms.name)
            self.logger.warning(warning_msg)
