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

import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Union, Sequence, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
from pandas import DataFrame

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg_dl.utils.bloomberg_dl_parser import BloombergDLParser
from qf_lib.data_providers.bloomberg_dl.utils.bloomberg_dl_session import BloombergDLSession
from qf_lib.data_providers.bloomberg_dl.utils.sse_client import SSEClient
from qf_lib.data_providers.futures_data_provider import FuturesDataProvider
from qf_lib.data_providers.helpers import normalize_data_array, cast_dataframe_to_proper_type
from qf_lib.data_providers.tickers_universe_provider import TickersUniverseProvider
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class BloombergDLDataProvider(AbstractPriceDataProvider, TickersUniverseProvider, FuturesDataProvider):
    HOST = "https://api.bloomberg.com"
    TIMEZONE = timezone.utc

    _IDENTIFIER_TYPE_MAP = {
        "ticker": "TICKER",
        "cusip": "CUSIP",
        "buid": "BB_UNIQUE",
        "bbgid": "BB_GLOBAL",
        "isin": "ISIN",
        "wpk": "WPK",
        "sedol1": "SEDOL",
        "common": "COMMON_NUMBER",
        "cins": "CINS",
        "cats": "CATS",
    }

    def __init__(self, settings: Settings, reply_timeout: int = 5, timer: Optional[Timer] = None,
                 save_to_disk: bool = False):
        super().__init__(timer=timer)

        self.parser = BloombergDLParser()
        self.reply_timeout: RelativeDelta = RelativeDelta(minutes=reply_timeout)
        self.save_to_disk = save_to_disk
        self.downloads_path = self._prepare_downloads_path(settings) if save_to_disk else None

        self._resource_lock = threading.Lock()

        self._terminal_identity_user = self._get_settings_attribute(settings.bbg_dl, "user")
        self._terminal_identity_sn = self._get_settings_attribute(settings.bbg_dl, "sn")

        try:
            self.session = BloombergDLSession(
                client_id=settings.bbg_dl.client_id,
                client_secret=settings.bbg_dl.client_secret,
            )
            catalog_id = self._discover_catalog_id()
            self.account_url = urljoin(self.HOST, f'/eap/catalogs/{catalog_id}/')
            self.logger.debug(f"Bloomberg DL REST API connection established - catalog: {catalog_id}")

        except Exception as exc:
            raise BloombergError(f"Failed to connect to Bloomberg DL REST API: {exc}") from exc

    @staticmethod
    def _prepare_downloads_path(settings: Settings):
        try:
            output_folder = "dl_responses"
            downloads_path: Optional[Path] = (
                    Path(get_starting_dir_abs_path()) / settings.output_directory / output_folder
            )
            downloads_path.mkdir(parents=True, exist_ok=True)
            return downloads_path
        except Exception as e:
            raise BloombergError(f"Error while creating downloads path: {e}")

    def get_history(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]],
                    fields: Union[str, Sequence[str]], start_date: datetime, end_date: Optional[datetime] = None,
                    frequency: Frequency = Frequency.DAILY,
                    currency: Optional[str] = None, pricing_source: Optional[str] = "BGN",
                    look_ahead_bias: bool = False, overrides: Optional[Dict[str, str]] = None,
                    **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        if frequency not in self.supported_frequencies():
            raise NotImplementedError(f"The provided frequency: {frequency} is not supported by the "
                                      f"{self.__class__.__name__}. To review the list of supported frequencies, please "
                                      f"consult the output of supported_frequencies() function.")

        original_end_date = (end_date or self.timer.now()) + RelativeDelta(second=0, microsecond=0)
        end_date = original_end_date if look_ahead_bias else self.get_end_date_without_look_ahead(original_end_date,
                                                                                                  frequency)
        start_date = self._adjust_start_date(start_date, frequency)
        got_single_date = self._got_single_date(start_date, original_end_date, frequency)

        fields, got_single_field = convert_to_list(fields, str)
        field_overrides = self._build_field_overrides(overrides)

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        actual_tickers = [self._current_ticker(t) for t in tickers]
        id_value_to_ticker = self._build_id_value_mapping(tickers, actual_tickers)
        tickers_str = [t.as_string() for t in actual_tickers]

        # Prepare the request payload
        request_payload = self._generate_request_payload(tickers_str, fields, True, pricing_source, field_overrides)
        request_payload['runtimeOptions'] = {
            '@type': 'HistoryRuntimeOptions',
            'period': str(frequency).lower(),
            'dateRange': {
                '@type': 'IntervalDateRange',
                'startDate': date_to_str(start_date),
                'endDate': date_to_str(end_date),
            },
        }
        if currency:
            request_payload['runtimeOptions']['historyPriceCurrency'] = currency

        data_array = self._submit_and_download(request_payload)
        if data_array is None:
            data_array = QFDataArray.create(dates=[], tickers=tickers, fields=fields)
        data_array = data_array.reindex(tickers=id_value_to_ticker.index).assign_coords(
            tickers=id_value_to_ticker.values)
        normalized_result = normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker,
                                                 got_single_field)
        return normalized_result

    def get_current_values(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]],
                           fields: Union[str, Sequence[str]],
                           overrides: Optional[Dict[str, str]] = None, pricing_source: Optional[str] = "BGN") -> \
            Union[None, float, str, list, QFSeries, QFDataFrame]:
        fields, got_single_field = convert_to_list(fields, str)
        field_overrides = self._build_field_overrides(overrides)

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        actual_tickers = [self._current_ticker(t) for t in tickers]
        tickers_str = [t.as_string() for t in actual_tickers]
        id_value_to_ticker = self._build_id_value_mapping(tickers, actual_tickers)

        request_payload = self._generate_request_payload(tickers_str, fields, False, pricing_source, field_overrides)
        data_frame = self._submit_and_download(request_payload)
        if data_frame is None:
            data_frame = QFDataFrame(columns=fields)

        data_frame.index = data_frame.index.map(id_value_to_ticker)
        data_frame = data_frame.reindex(index=tickers, columns=fields)

        # squeeze unused dimensions
        tickers_indices = 0 if got_single_ticker else slice(None)
        fields_indices = 0 if got_single_field else slice(None)
        squeezed_result = data_frame.iloc[tickers_indices, fields_indices]

        return cast_dataframe_to_proper_type(squeezed_result) if tickers_indices != 0 or fields_indices != 0 \
            else squeezed_result

    def get_tickers_universe(self, universe_ticker: BloombergTicker, date: Optional[datetime] = None,
                             display_figi: bool = False) -> List[BloombergTicker]:
        members_and_weights = self._get_index_members_and_weights(universe_ticker, date, display_figi)
        return members_and_weights.index.tolist()

    def get_tickers_universe_with_weights(self, universe_ticker: BloombergTicker, date: Optional[datetime] = None,
                                          display_figi: bool = False) -> QFSeries:
        return self._get_index_members_and_weights(universe_ticker, date, display_figi)

    def get_unique_tickers(self, universe_ticker: BloombergTicker) -> List[BloombergTicker]:
        raise NotImplementedError(f"{self.__class__.__name__} does not provide historical tickers_universe data")

    def price_field_to_str_map(self) -> Dict[PriceField, str]:
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

    @staticmethod
    def supported_frequencies():
        return {Frequency.DAILY, Frequency.WEEKLY, Frequency.MONTHLY, Frequency.QUARTERLY, Frequency.YEARLY}

    @staticmethod
    def _current_ticker(t: BloombergTicker):
        return t.get_current_specific_ticker() if isinstance(t, BloombergFutureTicker) else t

    def _generate_request_payload(self, tickers_str: Sequence[str], fields: Sequence[str], historical: bool,
                                  pricing_source: Optional[str], field_overrides):
        contains = [self._build_identifier_dict(t, field_overrides) for t in tickers_str]
        contains = [c for c in contains if c is not None]

        if len(contains) == 0:
            raise ValueError("No valid tickers were provided. Please refer to the logs and adjust your data request.")

        request_name = (f"r{datetime.now():%Y%m%d%H%M%S%f}"
                        f"{hashlib.md5(''.join(sorted(tickers_str + fields)).encode()).hexdigest()[:10]}")

        request_payload = {
            '@type': 'HistoryRequest' if historical else 'DataRequest',
            'name': request_name,
            'universe': {
                '@type': 'Universe',
                'contains': contains,
            },
            'fieldList': {
                '@type': 'HistoryFieldList' if historical else 'DataFieldList',
                'contains': [{'mnemonic': f for f in fields}],
            },
            'trigger': {'@type': 'SubmitTrigger'},
            'formatting': {
                '@type': 'MediaType',
                'outputMediaType': "application/json"
            }
        }

        if pricing_source:
            request_payload['pricingSourceOptions'] = {
                '@type': 'HistoryPricingSourceOptions' if historical else 'DataPricingSourceOptions',
                'prefer': {'mnemonic': pricing_source},
            }

        self._set_terminal_identity(request_payload)
        return request_payload

    def _get_futures_chain_dict(self, tickers: Union[BloombergFutureTicker, Sequence[BloombergFutureTicker]],
                                expiration_date_fields: Union[str, Sequence[str]],
                                universe_creation_time: datetime = None) -> Dict[FutureTicker, QFDataFrame]:
        tickers, _ = convert_to_list(tickers, BloombergFutureTicker)
        expiration_date_fields, _ = convert_to_list(expiration_date_fields, str)

        active_ticker_string_to_future_ticker = {
            future_ticker.get_active_ticker(): future_ticker for future_ticker in tickers
        }
        active_bbg_tickers = list(active_ticker_string_to_future_ticker.keys())

        field_overrides = {"CHAIN_DATE": datetime.now().strftime('%Y%m%d'), 'INCLUDE_EXPIRED_CONTRACTS': 'Y'}
        active_ticker_to_chain_tickers_list = self.get_current_values(active_bbg_tickers, "FUT_CHAIN",
                                                                      overrides=field_overrides).to_dict()
        future_ticker_to_chain_tickers_list = {
            active_ticker_string_to_future_ticker[active_ticker]: chain
            for active_ticker, chain in active_ticker_to_chain_tickers_list.items()
        }

        future_ticker_to_chain_tickers_list = {
            future_ticker: [BloombergTicker(s['SECURITY_DES'], future_ticker.security_type,
                                            future_ticker.point_value) for s in specific_tickers_strings_list]
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

    def _get_index_members_and_weights(self, universe_ticker: BloombergTicker, date: Optional[datetime] = None,
                                       display_figi: bool = False) -> QFSeries:
        date = date or datetime.now()
        if date.date() != datetime.today().date():
            raise ValueError(f"{self.__class__.__name__} does not provide historical tickers universe data")

        field = 'INDEX_MEMBERS_WEIGHTS'
        MAX_PAGE_NUMBER = 7
        MAX_MEMBERS_PER_PAGE = 3000
        universe = []

        def str_to_bbg_ticker(identifier: str, figi: bool):
            ticker_str = f"/bbgid/{identifier}" if figi else f"{identifier} Equity"
            return BloombergTicker(ticker_str, SecurityType.STOCK, 1)

        def cast_weight_to_float(weight: str):
            try:
                return float(weight)
            except (ValueError, TypeError):
                return float("nan")

        for page_no in range(1, MAX_PAGE_NUMBER + 1):
            ticker_data = self.get_current_values(universe_ticker, field, overrides={
                "DISPLAY_ID_BB_GLOBAL_OVERRIDE": "Y" if display_figi else "N",
                "PAGE_NUMBER_OVERRIDE": str(page_no)
            })

            df = QFDataFrame(ticker_data) if len(ticker_data) > 0 else QFDataFrame(
                columns=["TICKER_AND_EXCH_CODE", "PERCENT_WEIGHT"])
            df = df.set_index("TICKER_AND_EXCH_CODE").applymap(cast_weight_to_float)
            df.index = df.index.map(lambda s: str_to_bbg_ticker(s, display_figi))
            universe.append(df)
            if len(df) < MAX_MEMBERS_PER_PAGE:
                break

        universe_series = pd.concat(universe).iloc[:, 0]
        return universe_series

    def _build_formatting(self) -> dict:
        return {
            '@type': 'MediaType',
            'outputMediaType': "application/json"
        }

    def _submit_and_download(self, request_payload: dict):
        # Open SSE connection before submitting the request
        sse_url = urljoin(self.HOST, '/eap/notifications/content/responses')
        sse_client = SSEClient(sse_url, self.session)

        try:
            requests_url = urljoin(self.account_url, 'requests/')
            response = self.session.post(requests_url, json=request_payload, raise_on_error=False)
            resp_json = response.json()

            # Handle HTTP errors from request submission
            status_code = getattr(response, 'status_code', None)
            if status_code is not None and status_code >= 400:
                self._log_request_submission_error(status_code, resp_json)
                return None

            server_request_id = resp_json["request"].get("identifier")

            # Obtain the {field: fields_group} mapping from Bloomberg, used to infer fields' types
            fields_url = urljoin(self.account_url, f'requests/{server_request_id}/fieldList')
            fields_response = self.session.get(fields_url)
            field_mapping = {field['mnemonic']: field['type'] for field in fields_response.json().get('contains', [])}

            expiration = datetime.now(self.TIMEZONE) + self.reply_timeout
            while datetime.now(self.TIMEZONE) < expiration:
                event = sse_client.read_event()

                if event.is_heartbeat():
                    self.logger.debug('Received heartbeat event, keep waiting for events')
                    continue

                self.logger.info(f'Received reply delivery notification event: {event}')
                event_data = json.loads(event.data)

                if not self._event_matches_request(event_data, server_request_id):
                    self.logger.debug("Some other delivery occurred - continue waiting")
                    continue

                output_key = event_data['key']
                sse_client.disconnect()

                output_url = urljoin(self.HOST, f"{self.account_url}content/responses/{output_key}")
                self.logger.info(f"Response ready for '{server_request_id}' - downloading {output_key}")

                df = self._download_and_parse(output_url, server_request_id)
                request_type = event_data.get('metadata', {}).get('DL_REQUEST_TYPE', None)
                if request_type == 'HistoryRequest':
                    return self.parser.get_history(df, field_mapping)
                elif request_type == 'DataRequest':
                    return self.parser.get_current_values(df, field_mapping)
                else:
                    raise NotImplementedError("Currently only HistoryRequest and DataRequest are requests types "
                                              "are supported by the Bloomberg DL Data Provider.")

            self.logger.warning(f"Response for '{server_request_id}' not received within {self.reply_timeout} - "
                                f"returning empty")
            return None
        except Exception as e:
            self.logger.warning(f"Bloomberg DL request submission failed with the following exception:"
                                f" {e}. No response data can be obtained for this request.")
            return None
        finally:
            sse_client.disconnect()

    def _log_request_submission_error(self, status_code: int, resp_json: dict):
        title = resp_json.get('title', resp_json.get('error', 'Unknown Error'))
        description = resp_json.get('description', resp_json.get('error_description', ''))
        errors = resp_json.get('errors', [])
        msg = f"Bloomberg DL request submission failed with HTTP {status_code} ({title}): {description}"
        if errors:
            msg += f" Errors: {errors}"
        msg += " No response data can be obtained for this request."
        self.logger.warning(msg)

    @staticmethod
    def _event_matches_request(event_data: dict, server_request_id: str) -> bool:
        metadata = event_data.get('metadata', {})
        if server_request_id == metadata.get('DL_REQUEST_ID', ''):
            return True
        return False

    def _download_and_parse(self, output_url: str, request_id: str) -> DataFrame:
        with self.session.get(output_url, stream=True) as response:
            raw_bytes = response.content

            if self.save_to_disk and self.downloads_path is not None:
                file_path = self.downloads_path / f"{request_id}.json"
                file_path.write_bytes(raw_bytes)
                self.logger.debug(f"Response saved to {file_path}")

            return self.parser.decompress_response(raw_bytes)

    def _build_identifier_dict(self, ticker_str: str,
                               field_overrides: Optional[List[Dict]] = None) -> Optional[Dict]:
        id_type, id_value = self._parse_identifier(ticker_str)
        if id_type is None:
            return None

        identifier = {
            '@type': 'Identifier',
            'identifierType': id_type,
            'identifierValue': id_value,
        }
        if field_overrides:
            identifier['fieldOverrides'] = field_overrides
        return identifier

    @staticmethod
    def _build_field_overrides(overrides: Optional[Dict[str, str]]) -> Optional[List[Dict]]:
        if not overrides:
            return None
        return [
            {'@type': 'FieldOverride', 'mnemonic': mnemonic, 'override': value}
            for mnemonic, value in overrides.items()
        ]

    def _parse_identifier(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        identifier = f"/ticker/{identifier}" if not identifier.startswith("/") else identifier
        match = re.match(r"^/(\w+)/(.+)", identifier)
        if not match:
            self.logger.error(
                f"Detected incorrect identifier: {identifier}. It will be removed from the data request.\n"
                f"In order to provide an identifier, which is not a ticker, please use "
                f"'/id_type/identifier' format, with id_type being one of the following: "
                f"{list(self._IDENTIFIER_TYPE_MAP.values())}")
            return None, None

        id_type_key, id_value = match.groups()
        mapped = self._IDENTIFIER_TYPE_MAP.get(id_type_key.lower())
        if mapped is None:
            self.logger.error(f"Unknown identifier type '{id_type_key}' in '{identifier}'. "
                              f"Valid types: {list(self._IDENTIFIER_TYPE_MAP.values())}")
            return None, None

        return mapped, id_value

    def _build_id_value_mapping(self, tickers: Sequence[BloombergTicker],
                                actual_tickers: Sequence[BloombergTicker]) -> QFSeries:
        mapping = {}
        for original, actual in zip(tickers, actual_tickers):
            ticker_str = actual.as_string()
            _, id_value = self._parse_identifier(ticker_str)
            if id_value:
                mapping[id_value] = original
            mapping[ticker_str] = original

        return QFSeries([d for d in mapping.values()], index=[d for d in mapping.keys()])

    def _set_terminal_identity(self, payload: dict):
        """Inject terminalIdentity into payload when credentials are available."""
        user = self._parse_terminal_identity_user(self._terminal_identity_user)
        sn = self._parse_terminal_identity_sn(self._terminal_identity_sn)

        if sn and user is not None:
            payload["terminalIdentity"] = {
                "@type": "BlpTerminalIdentity",
                "userNumber": user,
                "serialNumber": sn[0],
                "workStation": sn[1],
            }
        elif user is not None:
            payload["terminalIdentity"] = {
                "@type": "BbaTerminalIdentity",
                "userNumber": user,
            }

    def _discover_catalog_id(self) -> str:
        """Discover the scheduled catalog identifier from the /eap/catalogs/ endpoint."""
        catalogs_url = urljoin(self.HOST, '/eap/catalogs/')
        response = self.session.get(catalogs_url)

        catalogs = response.json().get('contains', [])
        for catalog in catalogs:
            if catalog.get('subscriptionType') == 'scheduled':
                return catalog['identifier']

        self.logger.error('Scheduled catalog not in %r', response.json().get('contains', []))
        raise BloombergError('Scheduled catalog not found')

    def _get_settings_attribute(self, settings_obj, attribute: str):
        try:
            return getattr(settings_obj, attribute)
        except AttributeError:
            self.logger.warning(f"No {attribute} value found in the settings file, default (empty) value will be"
                                f" used instead.")
            return None

    @staticmethod
    def _parse_terminal_identity_user(raw_value):
        if raw_value is None:
            return None
        try:
            return int(raw_value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid terminal user '{raw_value}'. "
                             f"Obtain the User value by running IAM <GO> in Bloomberg terminal.")

    @staticmethod
    def _parse_terminal_identity_sn(raw_value):
        if raw_value is None:
            return None
        try:
            return [int(i) for i in str(raw_value).split("-")]
        except (ValueError, TypeError):
            raise ValueError(f"Invalid terminal S/N '{raw_value}'. "
                             f"Obtain the S/N value by running IAM <GO> in Bloomberg terminal.")
