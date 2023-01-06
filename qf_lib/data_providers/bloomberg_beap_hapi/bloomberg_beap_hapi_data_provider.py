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

import json
import os
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Union, Sequence, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.data_providers.tickers_universe_provider import TickersUniverseProvider

try:
    from beap_lib.beap_auth import Credentials, BEAPAdapter
    from beap_lib.sseclient import SSEClient

    is_beap_lib_installed = True
except ImportError:
    warnings.warn("No Bloomberg Beap HAPI installed. If you would like to use BloombergBeapHapiDataProvider first "
                  "install the beap_lib with all necessary dependencies.")
    is_beap_lib_installed = False

from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_fields_provider import \
    BloombergBeapHapiFieldsProvider
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser import BloombergBeapHapiParser
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_request_provider import \
    BloombergBeapHapiRequestsProvider
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_universe_provider import \
    BloombergBeapHapiUniverseProvider
from qf_lib.data_providers.helpers import normalize_data_array, cast_dataframe_to_proper_type
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class BloombergBeapHapiDataProvider(AbstractPriceDataProvider, TickersUniverseProvider):
    """
    Data Provider which provides financial data from Bloomberg BEAP HAPI.

    The settings file requires the following variables:
    - hapi_credentials.client_id
    - hapi_credentials.client_secret
    - hapi_credentials.expiration_date
    - output_directory

    Other optional settings parameters:
    - hapi_credentials.user (parameter to link the Data License to a Bloomberg Anywhere or Bloomberg Professional
    account; the User value can be obtained by running IAM <GO> in the Bloomberg terminal)
    - hapi_crenetials.sn (parameter to link the Data License to a Bloomberg Professional account;
    the S/N value can be obtained by running IAM <GO> in the Bloomberg terminal)
    """

    def __init__(self, settings: Settings, reply_timeout: int = 5):
        super().__init__()

        self.parser = BloombergBeapHapiParser()

        host = 'https://api.bloomberg.com'
        self.reply_timeout = timedelta(minutes=reply_timeout)  # reply_timeout - time in minutes

        output_folder = "hapi_responses"
        self.downloads_path = Path(get_starting_dir_abs_path()) / settings.output_directory / output_folder
        self.downloads_path.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()

        if is_beap_lib_installed:
            adapter = BEAPAdapter(Credentials.from_dict(
                {'client_id': settings.hapi_credentials.client_id,
                 'client_secret': settings.hapi_credentials.client_secret,
                 'expiration_date': settings.hapi_credentials.expiration_date}
            ))

            self.session.mount('https://', adapter)
            self.sse_client = self._get_sse_client(host, self.session)

            self.catalog_id = self._get_catalog_id(host)
            account_url = urljoin(host, f'/eap/catalogs/{self.catalog_id}/')
            trigger_url = urljoin(host, f"/eap/catalogs/{self.catalog_id}/triggers/prodDataStreamTrigger/")

            terminal_identity_user = self._get_settings_attribute(settings.hapi_credentials, "user")
            terminal_identity_sn = self._get_settings_attribute(settings.hapi_credentials, "sn")

            self.universe_hapi_provider = BloombergBeapHapiUniverseProvider(host, self.session, account_url)
            self.fields_hapi_provider = BloombergBeapHapiFieldsProvider(host, self.session, account_url)
            self.request_hapi_provider = BloombergBeapHapiRequestsProvider(host, self.session, account_url, trigger_url,
                                                                           terminal_identity_user, terminal_identity_sn)

            self.logger.info("Scheduled catalog URL: %s", account_url)
            self.logger.info("Scheduled trigger URL: %s", trigger_url)
            self.connected = True

        else:
            self.catalog_id = None
            self.universe_hapi_provider = None
            self.fields_hapi_provider = None
            self.request_hapi_provider = None
            self.connected = False

            self.logger.warning("Couldn't import the Data License API (beap_lib). Check if all the necessary "
                                "dependencies are installed.")

    def _get_settings_attribute(self, settings: Settings, attribute: str):
        try:
            return getattr(settings, attribute)
        except AttributeError:
            self.logger.warning(f"No {attribute} value found in the settings file, default (empty) value will be"
                                f" used instead. ")
            return None

    def _get_sse_client(self, host: str, session: requests.Session):
        """ Creates the SSEClient instance. """
        try:
            return SSEClient(urljoin(host, '/eap/notifications/sse'), session)
            # Catch an exception to get full error description with the help of the next GET request
        except requests.exceptions.HTTPError as err:
            self.logger.error(err)
            raise ConnectionError("Something went wrong connecting to the API. Try again later.")

    def _assert_is_connected(self):
        if not self.connected:
            raise BloombergError("Connection to the Bloomberg Data License service was not successful. Check if "
                                 "the library and all necessary dependencies are installed.")

    def get_history(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]], fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY,
                    universe_creation_time: Optional[datetime] = None, currency: Optional[str] = None) -> \
            Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical data from Bloomberg HAPI from the (start_date - end_date) time range.

        Parameters
        ----------
        tickers: BloombergTicker, Sequence[BloombergTicker]
            tickers for securities which should be retrieved
        fields: str, Sequence[str]
            fields of securities which should be retrieved
        start_date: datetime
            date representing the beginning of historical period from which data should be retrieved
        end_date: datetime
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used
        frequency: Frequency
            frequency of the data
        universe_creation_time: datetime
            Used only if we want to get previously created universe, fields universe or request
        currency: Optional[str]
            currency which should be used to obtain the historical data (by default local currency is used)

        Returns
        -------
        QFSeries, QFDataFrame, QFDataArray
            If possible the result will be squeezed, so that instead of returning QFDataArray, data of lower
            dimensionality will be returned. The results will be either an QFDataArray (with 3 dimensions: date, ticker,
            field), a QFDataFrame (with 2 dimensions: date, ticker or field; it is also possible to get 2 dimensions
            ticker and field if single date was provided) or QFSeries (with 1 dimensions: date).
            If no data is available in the database or an non existing ticker was provided an empty structure
            (QFSeries, QFDataFrame or QFDataArray) will be returned returned.

        Raises
        -------
        BloombergError
            When unexpected response from Bloomberg HAPI happened
        """
        self._assert_is_connected()

        end_date = end_date or datetime.now()
        end_date = end_date + RelativeDelta(second=0, microsecond=0)
        start_date = self._adjust_start_date(start_date, frequency)

        got_single_date = self._got_single_date(start_date, end_date, frequency)

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, str)

        tickers_str = [t.as_string() for t in tickers]
        universe_id = self._get_universe_id(tickers, universe_creation_time)
        universe_url = self.universe_hapi_provider.get_universe_url(universe_id, tickers_str, False)

        fields_list_id = self._get_fields_id(fields)
        fields_list_url, field_to_type = self.fields_hapi_provider.get_fields_history_url(fields_list_id, fields)

        # for requests - always create a new request with current time
        request_id = f'hReq{datetime.now():%m%d%H%M%S%f}'
        self.request_hapi_provider.create_request_history(request_id, universe_url, fields_list_url, start_date,
                                                          end_date, frequency, currency)
        self.logger.info(f'universe_id: {universe_id} fields_list_id: {fields_list_id} request_id: {request_id}')

        out_path = self._download_response(request_id)

        def current_ticker(t: BloombergTicker):
            return t.get_current_specific_ticker() if isinstance(t, BloombergFutureTicker) else t

        # Map each of the tickers in data array with corresponding ticker from tickers_mapping dictionary (in order
        # to support Future Tickers)
        tickers_mapping = {current_ticker(t).as_string(): t for t in tickers}
        data_array = self.parser.get_history(out_path, field_to_type, tickers_mapping)
        normalized_result = normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker,
                                                 got_single_field)

        return normalized_result

    def price_field_to_str_map(self, ticker: BloombergTicker = None) -> Dict[PriceField, str]:
        return {
            PriceField.Open: 'PX_OPEN',
            PriceField.High: 'PX_HIGH',
            PriceField.Low: 'PX_LOW',
            PriceField.Close: 'PX_LAST',
            PriceField.Volume: 'PX_VOLUME'
        }

    def expiration_date_field_str_map(self, ticker: BloombergTicker = None) -> Dict[ExpirationDateField, str]:
        return {
            ExpirationDateField.FirstNotice: "FUT_NOTICE_FIRST",
            ExpirationDateField.LastTradeableDate: "LAST_TRADEABLE_DT"
        }

    def supported_ticker_types(self):
        return {BloombergTicker, BloombergFutureTicker}

    def get_tickers_universe(self, universe_ticker: BloombergTicker, date: Optional[datetime] = None) -> List[BloombergTicker]:
        """
        Parameters
        ----------
        universe_ticker: BloombergTicker
            ticker that describes a specific universe, which members will be returned
        date: datetime
            date for which current universe members' tickers will be returned
        """
        date = date or datetime.now()
        if date.date() != datetime.today().date():
            raise ValueError(f"{self.__class__.__name__} does not provide historical tickers_universe data")

        field = 'INDX_MEMBERS'
        tickers: List[str] = self.get_current_values(universe_ticker, field)
        tickers = [BloombergTicker(f"{t} Equity", SecurityType.STOCK, 1) for t in tickers]
        return tickers

    def get_unique_tickers(self, universe_ticker: BloombergTicker) -> List[BloombergTicker]:
        raise ValueError(f"{self.__class__.__name__} does not provide historical tickers_universe data")

    def _get_futures_chain_dict(self, tickers: Union[BloombergFutureTicker, Sequence[BloombergFutureTicker]],
                                expiration_date_fields: Union[str, Sequence[str]],
                                universe_creation_time: datetime = None) -> Dict[FutureTicker, QFDataFrame]:
        """
        Returns tickers of futures contracts, which belong to the same futures contract chain as the provided ticker
        (tickers), along with their expiration dates using Bloomberg HAPI.

        Parameters
        ----------
        tickers: BloombergFutureTicker, Sequence[BloombergFutureTicker]
            future tickers for which future chains should be retrieved
        expiration_date_fields: ExpirationDateField, Sequence[ExpirationDateField]
            field that should be downloaded as the expiration date field
        universe_creation_time: datetime
            Used only if we want to get previously created universe, fields universe or request

        Returns
        -------
        Dict[BloombergFutureTicker, QFDataFrame]
            Dictionary mapping each BloombergFutureTicker to a QFSeries or QFDataFrame, containing specific future
            contracts tickers (BloombergTickers), indexed by these tickers

        Raises
        -------
        BloombergError
            When unexpected response from Bloomberg HAPI happened
        """
        self._assert_is_connected()

        tickers, got_single_ticker = convert_to_list(tickers, BloombergFutureTicker)
        expiration_date_fields, _ = convert_to_list(expiration_date_fields, ExpirationDateField)

        active_ticker_string_to_future_ticker = {
            future_ticker.get_active_ticker(): future_ticker for future_ticker in tickers
        }
        active_bbg_tickers = list(active_ticker_string_to_future_ticker.keys())

        field_overrides = [("CHAIN_DATE", datetime.now().strftime('%Y%m%d')), ('INCLUDE_EXPIRED_CONTRACTS', 'Y')]
        active_ticker_to_chain_tickers_list = self.get_current_values(active_bbg_tickers, "FUT_CHAIN",
                                                                      universe_creation_time, field_overrides).to_dict()
        future_ticker_to_chain_tickers_list = {
            active_ticker_string_to_future_ticker[active_ticker]: chain
            for active_ticker, chain in active_ticker_to_chain_tickers_list.items()
        }

        future_ticker_to_chain_tickers_list = {
            future_ticker: BloombergTicker.from_string(specific_tickers_strings_list, future_ticker.security_type,
                                                       future_ticker.point_value)
            for future_ticker, specific_tickers_strings_list in future_ticker_to_chain_tickers_list.items()
        }

        all_spec_tickers = [ticker for specific_tickers_list in future_ticker_to_chain_tickers_list.values()
                            for ticker in specific_tickers_list]
        futures_expiration_dates = self.get_current_values(all_spec_tickers, expiration_date_fields).dropna(how="all")

        def specific_futures_index(future_ticker) -> pd.Index:
            """
            Returns an Index of specific tickers for the given future ticker, which appeared in the futures
            expiration dates dataframe / series.
            """
            specific_tickers_list = future_ticker_to_chain_tickers_list[future_ticker]
            return futures_expiration_dates.index.intersection(specific_tickers_list)

        ticker_to_future_expiration_dates = {
            future_ticker: futures_expiration_dates.loc[specific_futures_index(future_ticker)]
            for future_ticker in tickers
        }

        return ticker_to_future_expiration_dates

    def get_current_values(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]],
                           fields: Union[str, Sequence[str]], universe_creation_time: datetime = None,
                           fields_overrides: Optional[List[Tuple]] = None) -> \
            Union[None, float, str, List, QFSeries, QFDataFrame]:
        """
        Gets from the Bloomberg HAPI the current values of fields for given tickers.

        Parameters
        ----------
        tickers: BloombergTicker, Sequence[BloombergTicker]
            tickers for securities which should be retrieved
        fields: str, Sequence[str]
            fields of securities which should be retrieved
        universe_creation_time: datetime
            Used only if we want to get previously created universe, fields universe or request
        fields_overrides: Optional[List[Tuple]]
            list of tuples representing overrides, where first element is always the name of the override and second
            element is the value e.g. in case if we want to download 'FUT_CHAIN' and include expired
            contracts we add the following overrides [('INCLUDE_EXPIRED_CONTRACTS', 'Y'),]

        Returns
        -------
        float, QFSeries, QFDataFrame
            Either QFDataFrame with 2 dimensions: ticker, field or QFSeries with 1 dimensions: ticker of field
            (depending if many tickers or fields were provided) is returned.

        Raises
        -------
        BloombergError
            When unexpected response from Bloomberg HAPI happened
        """
        self._assert_is_connected()
        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, str)

        tickers_str_to_obj = {t.as_string(): t for t in tickers}
        universe_id = self._get_universe_id(tickers, universe_creation_time)
        universe_url = self.universe_hapi_provider.get_universe_url(universe_id, list(tickers_str_to_obj.keys()),
                                                                    fields_overrides)

        fields_list_id = self._get_fields_id(fields)
        fields_list_url, field_to_type = self.fields_hapi_provider.get_fields_url(fields_list_id, fields)
        # for requests - always create a new request with current time
        request_id = f'cReq{datetime.now():%m%d%H%M%S%f}'

        # bulk format is ignored, but it gives response without column description - easier to parse
        self.request_hapi_provider.create_request(request_id, universe_url, fields_list_url)
        self.logger.info(f'universe_id: {universe_id} fields_list_id: {fields_list_id} request_id: {request_id}')

        out_path = self._download_response(request_id)
        data_frame = self.parser.get_current_values(out_path, field_to_type)

        # to keep the order of tickers and fields we reindex the data frame
        data_frame.index = [tickers_str_to_obj.get(x, BloombergTicker.from_string(x)) for x in data_frame.index]
        data_frame = data_frame.reindex(index=tickers, columns=fields)

        # squeeze unused dimensions
        tickers_indices = 0 if got_single_ticker else slice(None)
        fields_indices = 0 if got_single_field else slice(None)
        squeezed_result = data_frame.iloc[tickers_indices, fields_indices]

        return cast_dataframe_to_proper_type(squeezed_result) if tickers_indices != 0 or fields_indices != 0 \
            else squeezed_result

    def _get_universe_id(self, tickers: Sequence[BloombergTicker], creation_time: Optional[datetime] = None):
        universe_creation_time = creation_time or datetime.now()
        universe_id = f'uni{universe_creation_time:%m%d%H%M%S%f}'

        if len(tickers) == 1:
            ticker_str = tickers[0].as_string().lower().replace(" ", "")
            universe_id = ticker_str if ticker_str.isalnum() else universe_id

        return universe_id

    def _get_fields_id(self, fields: Sequence[str]):
        fields_list_id = f'flds{datetime.now():%m%d%H%M%S%f}'

        if len(fields) == 1:
            field_str = fields[0].replace("_", "")
            fields_list_id = field_str if field_str.isalnum() else fields_list_id
        elif fields == list(self.price_field_to_str_map().values()):
            fields_list_id = 'ohlcv'
        elif fields == list(self.expiration_date_field_str_map().values()):
            fields_list_id = 'futNoticeFirstLastTradeableDt'

        return fields_list_id

    def _download_response(self, request_id: str):
        expiration_timestamp = datetime.utcnow() + self.reply_timeout
        while datetime.utcnow() < expiration_timestamp:
            # Read the next available event
            event = self.sse_client.read_event()

            if event.is_heartbeat():
                self.logger.debug('Received heartbeat event, keep waiting for events')
                continue

            self.logger.info('Received reply delivery notification event: %s', event)
            event_data = json.loads(event.data)

            try:
                distribution = event_data['generated']
                reply_url = distribution['@id']

                distribution_id = distribution['identifier']
                catalog = distribution['snapshot']['dataset']['catalog']
                reply_catalog_id = catalog['identifier']
            except KeyError:
                self.logger.info("Received other event type, continue waiting")
            else:
                is_required_reply = '{}.bbg'.format(request_id) == distribution_id
                is_same_catalog = reply_catalog_id == self.catalog_id

                if not is_required_reply or not is_same_catalog:
                    self.logger.info("Some other delivery occurred - continue waiting. "
                                     "Reply catalog id: {}".format(reply_catalog_id))
                    continue

                output_file_path = os.path.join(self.downloads_path, distribution_id)
                out_path = self._download_distribution(reply_url, output_file_path)

                self.logger.info('Reply was downloaded, exit now')

                return out_path
        else:
            self.logger.warning('Reply NOT delivered, try to increase waiter loop timeout')

    def _download_distribution(self, url: str, out_path: str, chunk_size: int = 2048, stream: bool = True,
                               headers: Dict = None):
        """
        Function to download the data to an output directory.

        This function allows user to specify the output location of this download
        and works for a single endpoint.

        Note that 'Accept-Encoding: gzip, deflate' header added by default in a
        session to speed up downloading.

        Set 'chunk_size' to a larger byte size to speed up download process on
        larger downloads.
        """
        out_path += '.gz'

        with self.session.get(url, stream=stream, headers=headers) as response_:
            with open(out_path, 'wb') as out_file:
                for chunk in response_.raw.stream(chunk_size, decode_content=False):
                    out_file.write(chunk)
                self.logger.info('Downloaded %s to %s', url, out_file.name)
                return out_path

    def _get_catalog_id(self, host):
        catalogs_url = urljoin(host, '/eap/catalogs/')
        response = self.session.get(catalogs_url)

        # Extract a/the account number from the response
        if not response.ok:
            self.logger.error('Unexpected response status code: %s', response.status_code)
            raise BloombergError('Unexpected response')

        # We got back a good response. Let's extract our account number
        catalogs = response.json()['contains']
        for catalog in catalogs:
            if catalog['subscriptionType'] == 'scheduled':
                # Take the catalog having "scheduled" subscription type,
                # which corresponds to the Data License account number.f
                return catalog['identifier']

        # We exhausted the catalogs, but didn't find a non-'bbg' catalog.
        self.logger.error('Scheduled catalog not in %r', response.json()['contains'])
        raise BloombergError('Scheduled catalog not found')
