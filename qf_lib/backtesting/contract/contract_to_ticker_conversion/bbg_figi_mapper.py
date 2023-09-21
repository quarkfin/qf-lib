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

import asyncio
import itertools
import json
import re
from typing import List, Dict, Sequence, Union, Optional, Tuple
from urllib.error import HTTPError
from urllib.request import HTTPHandler, build_opener, Request

from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.helpers import grouper
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list


class BloombergTickerMapper(ContractTickerMapper):
    def __init__(self, openfigi_apikey: str = None, data_caching: bool = True):
        """

        The purpose of this class is to provide a mapping between various Bloomberg Tickers and other Ticker
        identifiers using the openFIGI API. It allows to map Bloomberg Tickers onto FIGI values.

        It is advised to always preload tickers mapping at the beginning, especially in case if the openFIGI API key
        is not provided.

        Important: In case of FIGI to Bloomberg Ticker mapping the POINT_VALUE parameter is not set!


        Parameters
        -----------
        openfigi_apikey: str
            API key for the openFIGI
        data_caching: bool
            if set to False, for each ticker to FIGI and FIGI to ticker mapping a request to openFIGI will be created
            and the data will not be stored in cache
        """
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self._openfigi_apikey = openfigi_apikey
        self._limit_timeout_seconds = 6 if openfigi_apikey else 60
        self._jobs_per_request = 100 if openfigi_apikey else 10
        self._openfigi_mapping_url = "https://api.openfigi.com/v3/mapping"

        self._enable_data_caching = data_caching
        self.ticker_to_contract_data = {}
        self.contract_data_to_ticker = {}

    def preload_tickers_mapping(self, tickers: Union[Sequence[BloombergTicker], BloombergTicker]):
        """
        Preloads ticker <-> FIGI mapping for a number of Bloomberg tickers and stores them in memory, so that
        they can be easily fetched using ticker_to_contract and contract_to_ticker functions, without sending additional
        requests to openFIGI.

        Parameters
        -----------
        tickers: Union[Sequence[BloombergTicker], BloombergTicker]
            ticker(s) for which the mapping should be fetched and saved
        """
        tickers, _ = convert_to_list(tickers, BloombergTicker)

        requests = [self._ticker_into_openfigi_requests(ticker) for ticker in tickers]
        results = asyncio.run(self._distribute_mapping_requests(requests))
        figi_values = map(lambda r: r.get('figi', None), itertools.chain(*results))

        self.ticker_to_contract_data.update(dict(zip(tickers, figi_values)))
        self.contract_data_to_ticker.update(dict(zip(figi_values, tickers)))

    def preload_figi_mapping(self, figis: Union[Sequence[str], str]):
        """
        Preloads ticker <-> FIGI mapping for a number of FIGI identifiers and stores them in memory, so that
        they can be easily fetched using ticker_to_contract and contract_to_ticker functions, without sending additional
        requests to openFIGI.

        Parameters
        -----------
        figis: Union[Sequence[str], str]
            FIGI(s) for which the mapping should be fetched and saved
        """
        figis, _ = convert_to_list(figis, str)

        requests = [{"idType": "ID_BB_GLOBAL", "idValue": f} for f in figis]
        results = itertools.chain(*asyncio.run(self._distribute_mapping_requests(requests)))
        mapping = dict(self._ticker_from_openfigi_response(r, f) for (r, f) in zip(results, figis))

        self.ticker_to_contract_data.update(mapping)
        self.contract_data_to_ticker.update({val: key for key, val in mapping.items()})

    def contract_to_ticker(self, figi: str) -> BloombergTicker:
        """ Maps Broker specific contract objects onto corresponding Tickers.

        Parameters
        ----------
        figi: str
            Financial Instrument Global Identifier (FIGI) of a security

        Returns
        -------
        BloombergTicker
            corresponding Bloomberg ticker
        """
        try:
            ticker = self.contract_data_to_ticker[figi]
        except KeyError:
            request = [{"idType": "ID_BB_GLOBAL", "idValue": figi}]
            result = asyncio.run(self._distribute_mapping_requests(request))[0][0]
            ticker, _ = self._ticker_from_openfigi_response(result, figi)
            if self._enable_data_caching:
                self.contract_data_to_ticker.update({figi: ticker})

        return ticker

    def ticker_to_contract(self, ticker: BloombergTicker) -> Optional[str]:
        """Maps ticker to corresponding ticker.

        Parameters
        ----------
        ticker: BloombergTicker
            ticker that should be mapped onto FIGI

        Returns
        -------
        str
            corresponding FIGI (Financial Instrument Global Identifier)
        """

        try:
            figi = self.ticker_to_contract_data[ticker]
        except KeyError:
            request = self._ticker_into_openfigi_requests(ticker)
            data = asyncio.run(self._distribute_mapping_requests([request]))[0][0]
            figi = data.get('figi', None)
            if self._enable_data_caching:
                self.ticker_to_contract_data.update({ticker: figi})

        return figi

    def _ticker_into_openfigi_requests(self, ticker: BloombergTicker) -> Dict[str, str]:
        sec_type_to_parameters = {
            SecurityType.STOCK: (["idValue", "exchCode", "marketSecDes"], r"^(.+) (\w+) (\w+)"),
            SecurityType.FUTURE: (["idValue", "marketSecDes"], r"^(.+ .+) (\w+)"),
            SecurityType.INDEX: (["idValue"], r"^(.+)"),
            SecurityType.FX: (["idValue"], r"^(.+) \w+")
        }

        try:
            parameters, match_params = sec_type_to_parameters[ticker.security_type]
            # Remove the /ticker/ part if applicable
            request = dict(zip(parameters, re.match(match_params, ticker.as_string().lstrip("/ticker/")).groups()))
            return {"idType": "TICKER", **request}
        except KeyError:
            raise ValueError(f"The {ticker.security_type} is not supported by the {self.__class__.__name__}.") from None
        except AttributeError:
            return {"idType": "TICKER", "idValue": ticker.as_string().lstrip("/ticker/")}

    def _ticker_from_openfigi_response(self, contract_data: Dict[str, str], figi: str) -> \
            Tuple[Optional[BloombergTicker], str]:
        security_type_map = {
            'Index': (SecurityType.INDEX, ['ticker']),
            'Equity': (SecurityType.STOCK, ['ticker', 'exchCode', 'marketSector']),
            'Mutual Fund': (SecurityType.STOCK, ['ticker', 'exchCode', 'marketSector']),
            'Future': (SecurityType.FUTURE, ['ticker', 'marketSector']),
            'CROSS': (SecurityType.FX, ['ticker', 'marketSector']),
            'SPOT': (SecurityType.FX, ['ticker', 'marketSector']),
        }

        try:
            security_type, fields = security_type_map[contract_data.get('securityType2', '')]
            fields_data = [contract_data.get(f) for f in fields if contract_data.get(f)]
            ticker_str = " ".join(fields_data)

            ticker = BloombergTicker(ticker_str, security_type)
            ticker.set_name(contract_data.get('name', None))
            return ticker, figi
        except KeyError:
            self.logger.warning(f"The '{contract_data.get('securityType2', '')}' security type is not supported by the "
                                f"{self.__class__.__name__}. The FIGI {figi} could not have been mapped properly.")
            return None, figi

    async def _distribute_mapping_requests(self, requests: Sequence):
        return await asyncio.gather(
            *[self._send_mapping_request(requests_chunk, i * self._limit_timeout_seconds)
              for i, requests_chunk in enumerate(grouper(self._jobs_per_request, requests))]
        )

    async def _send_mapping_request(self, request_content: List, delay: int = 0) -> List:
        await asyncio.sleep(delay)
        http_handler = HTTPHandler()
        opener = build_opener(http_handler)
        request = Request(self._openfigi_mapping_url, data=bytes(json.dumps(request_content), encoding="utf-8"),
                          method="POST")
        request.add_header("Content-Type", "application/json")
        if self._openfigi_apikey:
            request.add_header("X-OPENFIGI-APIKEY", self._openfigi_apikey)

        try:
            with opener.open(request) as response:
                if response.code == 200:
                    results = json.loads(response.read().decode("utf-8"))
                    return [r.get('data', [{}])[0] for r in results]

        except HTTPError as response:
            if response.code == 401:
                raise ConnectionError("The given API key is invalid.") from None
            elif response.code == 429:
                raise ConnectionError("Too Many Request. You have reached the rate limitations.") from None
            else:
                raise ConnectionError(f"The request failed with the  code: {response.code}.") from None

    def __str__(self):
        return self.__class__.__name__
