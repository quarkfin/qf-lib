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
import inspect
from abc import abstractmethod
from datetime import datetime
from typing import Union, Sequence, Optional

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.prefetching_data_provider import PrefetchingDataProvider


class DataHandler:
    """
    DataHandler is a wrapper which can be used with any AbstractPriceDataProvider in both live and backtest
    environment. It makes sure that data "from the future" is not passed into components in the backtest environment.

    DataHandler should be used by all the Backtester's components (even in the live trading setup).

    The goal of a DataHandler is to provide backtester's components with financial data. It makes sure that
    no data from the future (relative to a "current" time of a backtester) is being accessed, that is: that there
    is no look-ahead bias.

    Parameters
    -----------
    data_provider: AbstractPriceDataProvider
        the underlying data provider
    timer: Timer
        timer used to keep track of the data "from the future"
    """
    frequency = None

    def __init__(self, data_provider: DataProvider, timer: Timer):

        self._data_provider = data_provider
        self.__dict__['timer'] = timer

        self._check_frequency(data_provider.frequency)
        self.default_frequency = data_provider.frequency  # type: Frequency

        self.is_optimised = False

    @property
    def data_provider(self) -> DataProvider:
        """Property necessary to implement the look-ahead bias decorator functionality."""
        return self._data_provider

    def use_data_bundle(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                        start_date: datetime, end_date: datetime, frequency: Frequency = Frequency.DAILY):
        """
        Optimises running of the backtest. All the data will be downloaded before the backtest.
        Note that requesting during the backtest any other ticker or price field than the ones in the params
        of this function will result in an Exception.

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            ticker or sequence of tickers of the securities
        fields: PriceField, Sequence[PriceField]
            PriceField or sequence of PriceFields of the securities
        start_date: datetime
            initial date that should be downloaded
        end_date: datetime
            last date that should be downloaded
        frequency
            frequency of the data
        """
        assert not self.is_optimised, "Multiple calls on use_data_bundle() are forbidden"

        tickers, _ = convert_to_list(tickers, Ticker)
        fields, _ = convert_to_list(fields, PriceField)

        self._check_frequency(frequency)
        self.default_frequency = frequency

        self._data_provider = PrefetchingDataProvider(self.data_provider, tickers, fields, start_date,
                                                     end_date, frequency)
        self.is_optimised = True

    def __getattr__(self, attr):
        original_attr = self.data_provider.__getattribute__(attr)

        # Check if method is marked for date filtering
        if callable(original_attr) and hasattr(original_attr, 'date_parameters_to_adjust'):
            # Wrap only methods with _filter_dates specified
            def wrapper(*args, **kwargs):
                # Get the method signature to inspect parameter types
                sig = inspect.signature(original_attr)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                data_handler_variables = {}

                # Retrieve the specific parameters to check from the decorator
                param_names_to_filter = original_attr.date_parameters_to_adjust

                # Go through each specified argument and apply date filtering
                for param_name in param_names_to_filter:
                    if param_name in bound_args.arguments:
                        param_value = bound_args.arguments[param_name]
                        data_handler_variables[f"__original_{param_name}"] = param_value
                        param_value = self._get_end_date_without_look_ahead(param_value, self.frequency)
                        bound_args.arguments[param_name] = param_value

                # Call the original method with filtered arguments
                return original_attr(*bound_args.args, **bound_args.kwargs, **data_handler_variables)

            return wrapper
        else:
            return original_attr

    @abstractmethod
    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency = None,
                                 end_time: Optional[datetime] = None) -> Union[float, QFSeries]:
        pass

    @abstractmethod
    def _get_end_date_without_look_ahead(self, end_date: datetime, frequency: Frequency):
        pass

    @abstractmethod
    def _check_frequency(self, frequency):
        """ Verify if the provided frequency is compliant with the type of Data Handler used. """
        pass
