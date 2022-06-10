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

from pathlib import Path
from typing import Union, Sequence, Dict, List
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests
import pandas as pd
import warnings

from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker

try:
    from beap_lib.beap_auth import Credentials, BEAPAdapter
    from beap_lib.sseclient import SSEClient
except ImportError:
    warnings.warn("No Bloomberg Beap HAPI installed. If you would like to use BloombergBeapHapiDataProvider first "
                  "install modules from files")

from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_fields_provider import BloombergBeapHapiFieldsProvider
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser import BloombergBeapHapiParser
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_request_provider import BloombergBeapHapiRequestsProvider
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_universe_provider import BloombergBeapHapiUniverseProvider
from qf_lib.data_providers.helpers import normalize_data_array, cast_dataframe_to_proper_type
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class BloombergBeapHapiDataProvider(AbstractPriceDataProvider):
    """
    Data Provider which provides financial data from Bloomberg BEAP HAPI.
    """
    def __init__(self, settings: Settings, reply_timeout: int = 5):
        self.settings = settings
        self.credentials = Credentials.from_dict({'client_id': settings.hapi_credentials.client_id,
                                                  'client_secret': settings.hapi_credentials.client_secret,
                                                  'expiration_date': settings.hapi_credentials.expiration_date})  # type: Credentials
        host = 'https://api.bloomberg.com'

        adapter = BEAPAdapter(self.credentials)
        self.session = requests.Session()
        self.session.mount('https://', adapter)
        self.logger = qf_logger.getChild(self.__class__.__name__)
        try:
            self.sse_client = SSEClient(urljoin(host, '/eap/notifications/sse'), self.session)
        # Catch an exception to get full error description with the help of the next
        # GET request
        except requests.exceptions.HTTPError as err:
            self.logger.error(err)
            raise ConnectionError("Something went wrong connecting to the API. Try again later.")

        self.catalog_id = self._get_catalog_id(host)
        account_url = urljoin(host, '/eap/catalogs/{c}/'.format(c=self.catalog_id))
        self.logger.info("Scheduled catalog URL: %s", account_url)
        trigger_url = urljoin(host, '/eap/catalogs/{c}/triggers/prodDataStreamTrigger/'.format(c=self.catalog_id))
        self.logger.info("Scheduled trigger URL: %s", trigger_url)

        self.universe_hapi_provider = BloombergBeapHapiUniverseProvider(host, self.session, account_url)
        self.fields_hapi_provider = BloombergBeapHapiFieldsProvider(host, self.session, account_url)
        self.request_hapi_provider = BloombergBeapHapiRequestsProvider(host, self.session, account_url, trigger_url)

        self.reply_timeout = timedelta(minutes=reply_timeout)  # reply_timeout - time in minutes

        output_folder = "hapi_responses"

        self.downloads_path = Path(get_starting_dir_abs_path()) / self.settings.output_directory / output_folder
        self.downloads_path.mkdir(parents=True, exist_ok=True)

        self.parser = BloombergBeapHapiParser()

    def get_history(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]], fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY,
                    universe_creation_time: datetime = None) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical data from Bloomberg HAPI from the (start_date - end_date) time range.

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
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

        if fields is None:
            raise ValueError("Fields being None is not supported by {}".format(self.__class__.__name__))

        end_date = end_date or datetime.now()
        end_date = end_date + RelativeDelta(second=0, microsecond=0)
        start_date = self._adjust_start_date(start_date, frequency)

        got_single_date = self._got_single_date(start_date, end_date, frequency)

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, str)

        tickers_str = [t.as_string() for t in tickers]

        if universe_creation_time:
            universe_creation_time = datetime.strptime(universe_creation_time, "%Y%m%d%H%M")
        else:
            universe_creation_time = str(datetime.now().strftime("%Y%m%d%H%M"))

        universe_id = 'historyUniverse' + universe_creation_time
        universe_url = self.universe_hapi_provider.get_universe_url(universe_id, tickers_str, fieldsOverrides=False)

        # in most cases we will use only ohlcv fields - we can reuse fields
        if fields == ['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST', 'PX_VOLUME']:
            fieldlist_id = 'ohlcv'
        else:
            fieldlist_id = 'historyFields' + str(datetime.now().strftime("%Y%m%d%H%M"))

        fieldlist_url = self.fields_hapi_provider.get_fields_history_url(fieldlist_id, fields)

        # for requests - always create a new request with current time
        request_id = 'hRequest' + str(datetime.now().strftime("%Y%m%d%H%M"))
        self.request_hapi_provider.create_request_history(request_id, universe_url, fieldlist_url, start_date, end_date, frequency)

        self.logger.info('universe_id: {} fieldlist_id: {} request_id: {}'.format(universe_id, fieldlist_id, request_id))

        out_path = self._download_response(request_id)

        data_array = self.parser.get_history(out_path)

        tickers_mapping = {t.as_string(): t for t in tickers}

        # Map each of the tickers in data array with corresponding ticker from tickers_mapping dictionary (in order
        # to support Future Tickers)
        def _map_ticker(ticker):
            try:
                return tickers_mapping[ticker]
            except KeyError:
                return ticker

        data_array = data_array.assign_coords(tickers=[_map_ticker(t) for t in data_array.tickers.values])

        normalized_result = normalize_data_array(
            data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field)

        return normalized_result

    def price_field_to_str_map(self, ticker: BloombergTicker = None) -> Dict[PriceField, str]:
        price_field_dict = {
            PriceField.Open: 'PX_OPEN',
            PriceField.High: 'PX_HIGH',
            PriceField.Low: 'PX_LOW',
            PriceField.Close: 'PX_LAST',
            PriceField.Volume: 'PX_VOLUME'
        }
        return price_field_dict

    def expiration_date_field_str_map(self, ticker: BloombergTicker = None) -> Dict[ExpirationDateField, str]:
        expiration_date_field_dict = {
            ExpirationDateField.FirstNotice: "FUT_NOTICE_FIRST",
            ExpirationDateField.LastTradeableDate: "LAST_TRADEABLE_DT"
        }
        return expiration_date_field_dict

    def supported_ticker_types(self):
        return {BloombergTicker, BloombergFutureTicker}

    def _get_futures_chain_dict(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
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

        tickers, got_single_ticker = convert_to_list(tickers, BloombergFutureTicker)
        expiration_date_fields, got_single_expiration_date_field = convert_to_list(expiration_date_fields,
                                                                                   ExpirationDateField)

        if universe_creation_time:
            universe_creation_time = datetime.strftime(universe_creation_time, "%Y%m%d%H%M")
        else:
            universe_creation_time = str(datetime.now().strftime("%Y%m%d%H%M"))

        future_ticker_to_chain_tickers_list = self._get_list_of_tickers_in_the_future_chain(
            tickers, universe_creation_time)  # type: Dict[BloombergFutureTicker, List[BloombergTicker]]

        def get_futures_expiration_dates(specific_tickers: Union[BloombergTicker, Sequence[BloombergTicker]]) -> \
                Union[QFSeries, QFDataFrame]:
            """
            For a ticker (tickers) it returns a QFSeries or QFDataFrame consisting of the expiration dates fields of
            Future Contracts, that are defined by the given tickers.

            Parameters
            ----------
            specific_tickers
                tickers for which the expiration dates of future contracts should be retrieved

            Returns
            -------
            QFDataFrame
                Container containing all the dates, indexed by tickers
            """
            exp_dates = self.get_current_values(specific_tickers, expiration_date_fields)  # type: QFDataFrame

            # Drop these futures, for which no expiration date was found and cast all string dates into datetime
            return exp_dates.dropna(how="all").astype('datetime64[ns]')

        all_specific_tickers = [ticker for specific_tickers_list in future_ticker_to_chain_tickers_list.values()
                                for ticker in specific_tickers_list]

        futures_expiration_dates = get_futures_expiration_dates(all_specific_tickers)

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
                           fields: Union[str, Sequence[str]], universe_creation_time: datetime = None) -> Union[None, float, QFSeries, QFDataFrame]:
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

        Returns
        -------
        QFDataFrame/QFSeries
            Either QFDataFrame with 2 dimensions: ticker, field or QFSeries with 1 dimensions: ticker of field
            (depending if many tickers or fields were provided) is returned.

        Raises
        -------
        BloombergError
            When unexpected response from Bloomberg HAPI happened
        """
        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, str)

        tickers_str = [t.as_string() for t in tickers]

        if universe_creation_time:
            universe_creation_time = datetime.strptime(universe_creation_time, "%Y%m%d%H%M")
        else:
            universe_creation_time = str(datetime.now().strftime("%Y%m%d%H%M"))

        universe_id = 'currentUniverse' + universe_creation_time
        universe_url = self.universe_hapi_provider.get_universe_url(universe_id, tickers_str, fieldsOverrides=False)

        # in most cases we will use only two fields: 'FUT_NOTICE_FIRST', 'LAST_TRADEABLE_DT' - we can reuse fields
        if fields == ['FUT_NOTICE_FIRST', 'LAST_TRADEABLE_DT']:
            fieldlist_id = 'futNoticeFirstLastTradeableDt'
        else:
            fieldlist_id = 'currentFields' + str(datetime.now().strftime("%Y%m%d%H%M"))

        fieldlist_url = self.fields_hapi_provider.get_fields_url(fieldlist_id, fields)

        # for requests - always create a new request with current time
        request_id = 'cRequest' + str(datetime.now().strftime("%Y%m%d%H%M"))
        self.request_hapi_provider.create_request(request_id, universe_url, fieldlist_url, bulk_format_type=False)  # bulk format is ignored, but it gives response without column descirpition - easier to parse

        self.logger.info('universe_id: {} fieldlist_id: {} request_id: {}'.format(universe_id, fieldlist_id, request_id))

        out_path = self._download_response(request_id)

        data_frame = self.parser.get_current_values_dates_fields_format(out_path)

        # to keep the order of tickers and fields we reindex the data frame
        data_frame.index = [BloombergTicker(x) for x in data_frame.index]
        data_frame = data_frame.reindex(index=tickers, columns=fields)

        # squeeze unused dimensions
        tickers_indices = 0 if got_single_ticker else slice(None)
        fields_indices = 0 if got_single_field else slice(None)
        squeezed_result = data_frame.iloc[tickers_indices, fields_indices]

        casted_result = cast_dataframe_to_proper_type(squeezed_result)

        return casted_result

    def _get_list_of_tickers_in_the_future_chain(self,
                                                 tickers: Union[BloombergFutureTicker, Sequence[BloombergFutureTicker]],
                                                 universe_creation_time: str):

        active_ticker_string_to_future_ticker = {
            future_ticker.get_active_ticker().ticker: future_ticker for future_ticker in tickers
        }

        # Define mapping functions from strings into BloombergFutureTickers and BloombergTickers
        def future_ticker_from_string(active_ticker_string: str) -> BloombergFutureTicker:
            return active_ticker_string_to_future_ticker[active_ticker_string]

        universe_id = 'u' + universe_creation_time
        universe_url = self.universe_hapi_provider.get_universe_url(universe_id, active_ticker_string_to_future_ticker,
                                                                    fieldsOverrides=True)

        fieldlist_id = 'fieldsFutChain'
        fieldlist_url = self.fields_hapi_provider.get_fields_url(fieldlist_id, "FUT_CHAIN")

        # for requests - always create a new request with current time
        request_id = 'fc' + str(datetime.now().strftime("%Y%m%d%H%M"))
        self.request_hapi_provider.create_request(request_id, universe_url, fieldlist_url, bulk_format_type=True)

        self.logger.info('universe_id: {} fieldlist_id: {} request_id: {}'.format(universe_id, fieldlist_id, request_id))

        out_path = self._download_response(request_id)

        future_ticker_str_to_chain_tickers_str_list = self.parser.get_chain(out_path)

        future_ticker_to_chain_tickers_str_list = {
            future_ticker_from_string(future_ticker_str): specific_tickers_strings_list
            for future_ticker_str, specific_tickers_strings_list in future_ticker_str_to_chain_tickers_str_list.items()
        }

        future_ticker_str_to_chain_tickers_list = {
            future_ticker: BloombergTicker.from_string(specific_tickers_strings_list, future_ticker.security_type,
                                                       future_ticker.point_value)
            for future_ticker, specific_tickers_strings_list in future_ticker_to_chain_tickers_str_list.items()
        }

        # Check if for all of the requested tickers the futures chains were returned, and if not - log an error
        lacking_tickers = set(tickers).difference(future_ticker_str_to_chain_tickers_list.keys())

        if lacking_tickers:
            lacking_tickers_str = [t.name for t in lacking_tickers]
            error_message = "The requested futures chains for the BloombergFutureTickers {} could not have been " \
                            "downloaded successfully".format(lacking_tickers_str)
            self.logger.error(error_message)

            for ticker in lacking_tickers:
                future_ticker_str_to_chain_tickers_list[ticker] = []

        return future_ticker_str_to_chain_tickers_list

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
