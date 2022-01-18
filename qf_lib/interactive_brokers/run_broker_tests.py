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
from datetime import datetime, time
from time import sleep

from pandas import to_datetime

from data_providers.db_connection_provider import ReadOnlyPF, ReadWriteDBConnectionPF
from data_providers.internal_db.base_classes import InternalDBBase
from data_providers.internal_db.internal_db_data_provider import InternalDBDataProvider
from qf_common.config.ioc import container
from qf_lib.backtesting.contract.contract_to_ticker_conversion.ib_bloomberg_mapper import \
    IBBloombergContractTickerMapper, IBParameters
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.interactive_brokers.ib_broker import IBBroker
from qf_lib.settings import Settings
from scripts.interactive_brokers.ib_db_transaction_recorder import IBDBTransactionsRecorder
from strategies.cta_strategy.cta_tickers_universe import DAYS_BEFORE_EXP_DATE, non_agricultural_commodities, \
    agricultural_commodities, rates, tickers_selection, equities
from strategies.cta_strategy.ticker_ib_mapping import non_agricultural_commodities_map, agricultural_commodities_map, \
    rates_map, equities_map


def main():
    settings = container.resolve(Settings)
    db_connection_provider = ReadOnlyPF(settings)
    data_provider = InternalDBDataProvider()
    data_provider.set_db_connection_provider(db_connection_provider)

    # ticker = BloombergFutureTicker('Copper', 'HG{} Comdty', 1, DAYS_BEFORE_EXP_DATE, 250, "HKNUZ")

    dict = {**rates_map, **agricultural_commodities_map, **non_agricultural_commodities_map, **equities_map}
    contract_ticker_mapper = IBBloombergContractTickerMapper(dict, data_provider)
    broker = IBBroker(clientId=2)

    #print(broker.get_portfolio_value())
    db_connection_provider = container.resolve(ReadWriteDBConnectionPF)
    InternalDBBase.metadata.create_all(db_connection_provider.engine)
    #print("recorder ready")
    tickers = [BloombergFutureTicker('US Treasury Note, 10Yr', 'TY{} Comdty', 1, 1, 1000),
               BloombergFutureTicker('Silver', 'SI{} Comdty', 1, 1, 5000)]
    for ticker in tickers:
        try:
            ticker.initialize_data_provider(SettableTimer(datetime.now()), data_provider)

            contract = contract_ticker_mapper.ticker_to_contract(ticker.get_current_specific_ticker())
            #print(broker.get_portfolio_value())
            #details = broker.get_contract_details(contract)
            #multiplier = int(details.contract.multiplier) / details.priceMagnifier
            #p = data_provider.get_price(ticker.get_current_specific_ticker(), PriceField.Close, datetime.now() - RelativeDelta(days=10),
            #                            datetime.now(),).iloc[-1]

            #print(f"Ticker: {ticker.as_string()}, pt value {ticker.point_value}, 'multiplier' {multiplier}\n"      f"last bbg price: {p}")
            #print(f"{ticker.as_string()}, {ticker.point_value}, {details.contract.localSymbol}, "
                  #f"{details.contract.symbol}, {details.contract.multiplier},"
                  #f" {details.priceMagnifier}, {p},")

            # print(broker.get_liquid_hours(contract))
            print(ticker.name)
            order = Order(contract, 2, MarketOrder(), TimeInForce.DAY)
            #x = broker.place_orders([order])

            positions = broker.get_positions()
            for pos in positions:
                if pos.quantity() != 0:

                    print(pos)
                    c = pos.contract()
                    t = contract_ticker_mapper.contract_to_ticker(c)
                    order = Order(contract_ticker_mapper.ticker_to_contract(t),
                                  -pos.quantity(), MarketOrder(), TimeInForce.DAY)
                    broker.place_orders([order])
                    sleep(5)
                    print("placed")

            #print(order_ids)
            # broker.cancel_all_open_orders()

        except:
            pass

    print("finished")
    broker.stop()


if __name__ == '__main__':
    main()
