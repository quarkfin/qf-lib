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
import json
from typing import List, Dict, Sequence, Union
from urllib.request import HTTPHandler, build_opener, Request

from more_itertools import grouper

from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list

_sem = asyncio.Semaphore(1)


class BloombergFIGIMapper(ContractTickerMapper):
    def __init__(self, openfigi_apikey: str = None, data_caching: bool = True):
        """

        Parameters
        -----------
        openfigi_apikey: str
        data_caching: bool
        """
        self._openfigi_apikey = openfigi_apikey
        self._limit_timeout_seconds = 6 if openfigi_apikey else 6 #0
        self._jobs_per_request = 100 if openfigi_apikey else 1 #0
        self._openfigi_mapping_url = "https://api.openfigi.com/v3/mapping"

        self._enable_data_caching = data_caching
        self._ticker_to_contract = {}

    def preload_tickers_mapping(self, tickers: Union[Sequence[BloombergTicker], BloombergTicker]):
        tickers, _ = convert_to_list(tickers, BloombergTicker)

        jobs = [self._ticker_into_chunks(ticker) for ticker in tickers]
        results = asyncio.run(self._distribute_mapping_requests(jobs))

        print("AAAAAA")
        print(results)

    def _ticker_into_chunks(self, ticker: BloombergTicker):
        # TODO remove the /ticker/ or /bbgid/ part
        ticker_components = ticker.as_string().split(" ")
        if len(ticker_components) == 3:
            parameters = ["idType", "idValue", "exchCode", "marketSecDes"]
        else:
            parameters = ["idType", "idValue", "marketSecDes"]

        return dict(zip(parameters, ["TICKER", *ticker_components]))

    async def _distribute_mapping_requests(self, jobs):
        x = await asyncio.gather(
            *[self._send_mapping_request(request, i * self._limit_timeout_seconds)
              for i, request in enumerate(grouper(jobs, self._jobs_per_request))]
        )
        return x

    async def _send_mapping_request(self, request_content: List[Dict], delay: int = 0) -> Dict:
        await asyncio.sleep(delay)
        print("Starting the map request")
        http_handler = HTTPHandler()
        opener = build_opener(http_handler)
        request = Request(self._openfigi_mapping_url, data=bytes(json.dumps(request_content), encoding="utf-8"),
                          method="POST")
        request.add_header("Content-Type", "application/json")
        if self._openfigi_apikey:
            request.add_header("X-OPENFIGI-APIKEY", self._openfigi_apikey)

        with opener.open(request) as response:
            if response.code == 200:
                results = json.loads(response.read().decode("utf-8"))
                return results  # return a nice dictionary
            else:
                pass  # TODO handle different errors

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
        pass

    def ticker_to_contract(self, ticker: BloombergTicker) -> str:
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

        # Load data to the dict or not

    def __str__(self):
        return self.__class__.__name__


if __name__ == '__main__':
    BloombergFIGIMapper().preload_tickers_mapping([BloombergTicker("IBM US Equity"), BloombergTicker("SPY US Equity"),
                                                   BloombergTicker("RTY Index")])



