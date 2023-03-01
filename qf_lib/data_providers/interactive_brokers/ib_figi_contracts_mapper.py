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
from threading import Thread, Event, Lock
from typing import Optional, Dict
from ibapi.client import EClient
from qf_lib.backtesting.contract.contract_to_ticker_conversion.ib_contract_ticker_mapper import IBContractTickerMapper
from qf_lib.brokers.ib_broker.ib_contract import IBContract
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.logging.qf_parent_logger import ib_logger
from qf_lib.brokers.ib_broker.ib_wrapper import IBWrapper


class IBFIGItoIBContractMapper:
    """
    IB IBFIGItoIBContractMapper mapper that can be used to map FIGI defined IB contracts to the more specific ones.
    It is possible to define contracts like in the example for AAPL:

    ib_contract = IBContract()
    ib_contract.secIdType = "FIGI"
    ib_contract.secId = "BBG000B9XRY4"
    ib_contract.exchange = "SMART"

    However, some functionality like requesting historical data does not work with FIGI identifiers at this point.
    Therefore mapping of FIGI contracts to the more general IB Contacts is required. This class might be removed in
    the future when IB will add support to use FIGI contracts for the rest purposes.

    Parameters
    ----------
    clientId: int
        id of the Broker client
    host: str
        IP address
    port: int
        socket port
    """

    def __init__(self, clientId: int = 0, host: str = "127.0.0.1", port: int = 7497):

        self.logger = ib_logger.getChild(self.__class__.__name__)
        # Lock that synchronizes entries into the functions and makes sure we have a synchronous communication
        # with the client
        self.lock = Lock()

        self.waiting_time = 30  # expressed in seconds
        # Lock that informs us that wrapper received the response
        self.action_event_lock = Event()
        self.wrapper = IBWrapper(self.action_event_lock, IBContractTickerMapper({}))  # not necessary to have configured IBContractTickerMapper for FIGI contracts mapping
        self.client = EClient(wrapper=self.wrapper)
        self.clientId = clientId
        self.client.connect(host, port, self.clientId)

        # Run the client in the separate thread so that the execution of the program can go on
        # now we will have 3 threads:
        # - thread of the main program
        # - thread of the client
        # - thread of the wrapper
        thread = Thread(target=self.client.run)
        thread.start()

        # This will be released after the client initialises and wrapper receives the nextValidOrderId
        if not self._wait_for_results():
            raise ConnectionError("IB IBFIGItoIBContractMapper was not initialized correctly")

    def get_ticker_to_contract_mapping_from_figi_contracts(self, ticker_to_contract: Dict[Ticker, IBContract]) -> Dict[Ticker, IBContract]:
        """"
        Function to map dictionary:
            ticker -> ib_figi_contract
        to the dictionary:
            ticker -> ib_contract

        Parameters
        ----------
        ticker_to_contract: Dict[Ticker, IBContract]
            mapping between Tickers and parameters that should be used for these tickers, when transforming them into
            IBContracts (FIGI secIdType).

        Returns
        -------
        Dict[Ticker, Contract]
            mapping between Tickers and IB Contracts
        """
        new_ticker_to_contract_mapping = {}
        reqId = 0
        for ticker, contract in ticker_to_contract.items():
            contract_details = self._get_contract_details(reqId, contract)
            if contract_details:
                new_ticker_to_contract_mapping[ticker] = IBContract.from_string(str(contract_details.contract))
            else:
                self.logger.info(f'Could not find corresponding contract details for the ticker {ticker} and contract '
                                 f'{contract}. Using FIGI contract instead')
                new_ticker_to_contract_mapping[ticker] = contract
        return new_ticker_to_contract_mapping

    def stop(self):
        """ Stop the IBFIGItoIBContractMapper client and disconnect from the interactive brokers. """
        with self.lock:
            self.client.disconnect()
            self.logger.info("Disconnecting from the interactive brokers client")

    def _get_contract_details(self, reqId, contract):
        with self.lock:
            self.wrapper.reset_contract_details()
            self._reset_action_lock()
            self.client.reqContractDetails(reqId, contract)

            if self._wait_for_results(self.waiting_time):
                return self.wrapper.contract_details
            else:
                error_msg = f'Time out while getting positions for contract {contract}'
                self.logger.error(error_msg)

    def _wait_for_results(self, waiting_time: Optional[int] = None) -> bool:
        """ Wait for self.waiting_time """
        waiting_time = waiting_time or self.waiting_time
        wait_result = self.action_event_lock.wait(waiting_time)
        return wait_result

    def _reset_action_lock(self):
        """ threads calling wait() will block until set() is called"""
        self.action_event_lock.clear()
