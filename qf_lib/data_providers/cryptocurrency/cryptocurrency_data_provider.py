from datetime import date, datetime
from typing import Dict, Optional, Sequence, Union

import pandas as pd
from bs4 import BeautifulSoup as BS
from requests import Session

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import CcyTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.helpers import normalize_data_array, \
    tickers_dict_to_data_array, get_fields_from_tickers_data_dict


class CryptoCurrencyDataProvider(AbstractPriceDataProvider):
    """
    Constructs a new ``CryptoCurrencyDataProvider`` instance
    """

    DATE_COLUMN = 'Date'

    def __init__(self):
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self.earliest_api_date = datetime(2013, 4, 28)

    def get_history(self, tickers: Union[CcyTicker, Sequence[CcyTicker]],
                    fields: Union[None, str, Sequence[str]] = None,
                    start_date: datetime = None, end_date: datetime = None, **kwargs) \
            -> Union[QFSeries, QFDataFrame, QFDataArray]:
        tickers, got_single_ticker = convert_to_list(tickers, CcyTicker)
        got_single_date = (start_date == end_date)

        if fields is not None:
            fields, got_single_field = convert_to_list(fields, (PriceField, str))
        else:
            got_single_field = False  # all existing fields will be present in the result

        tickers_data_dict = {}
        with Session() as session:
            for ticker in tickers:
                single_ticker_data = self._get_single_ticker(ticker, fields, start_date, end_date, session)
                tickers_data_dict[ticker] = single_ticker_data

        if fields is None:
            fields = get_fields_from_tickers_data_dict(tickers_data_dict)

        result_data_array = tickers_dict_to_data_array(tickers_data_dict, tickers, fields)
        result = normalize_data_array(result_data_array, tickers, fields,
                                      got_single_date, got_single_ticker, got_single_field)
        return result

    def supported_ticker_types(self):
        return {CcyTicker}

    def price_field_to_str_map(self, ticker: CcyTicker = None) -> Dict[PriceField, str]:
        return {
            PriceField.Open: 'Open',
            PriceField.High: 'High',
            PriceField.Low: 'Low',
            PriceField.Close: 'Close',
            PriceField.Volume: 'Volume'
        }

    def _get_single_ticker(self, ticker: CcyTicker, fields: Sequence[str],
                           start_date: datetime, end_date: datetime, session: Session) -> Optional[pd.DataFrame]:
        """
        Contacts the API and gets the price data for a single ticker
        """
        if end_date is None:
            end_date = date.today()

        if start_date is None:
            start_date = self.earliest_api_date
        elif start_date < self.earliest_api_date:
            self.logger.warning(
                "This date is earlier than the earliest records on the API. Using the earliest possible date "
                "instead (2013-04-28)"
            )

        data_url = "http://coinmarketcap.com/currencies/{ticker_str}/historical-data/?" \
                   "start={start_date_str}&end={end_date_str}".format(
                        ticker_str=ticker.as_string(),
                        start_date_str=start_date.strftime("%Y%m%d"),
                        end_date_str=end_date.strftime("%Y%m%d")
                   )

        request = session.get(data_url)

        if request.status_code is not 200:
            if request.status_code == 404:
                self.logger.error("The ticker {} does not exist on the API".format(ticker.as_string()))
            else:
                raise ConnectionError("Something went wrong connecting to the API. Try again later.")

            return None
        else:
            result_df = self._parse_request(request, fields)
            return result_df

    def _parse_request(self, request, fields):
        table = BS(request.content, 'lxml').table
        if table is None:
            raise AttributeError(
                "No data was found for the ticker. This could be an error on the API, or they may have changed their "
                "layout format."
            )
        headersHTML = table.findAll('th')

        column_names = [header.string.replace('*', '') for header in headersHTML]
        idx_of_date_column = column_names.index(self.DATE_COLUMN)

        relevant_fields_set = set(fields).union({self.DATE_COLUMN})
        relevant_fields_indices = []
        field_names = []
        for idx, col_name in enumerate(column_names):
            if col_name in relevant_fields_set:
                relevant_fields_indices.append(idx)

                if idx != idx_of_date_column:
                    field_names.append(col_name)

        dates = []
        data = []

        data_rows = table.findAll('tr')
        for row in data_rows[1:]:
            rows_date, numeric_values = self._parse_data_row(row, relevant_fields_indices, idx_of_date_column)
            dates.append(rows_date)
            data.append(numeric_values)

        return pd.DataFrame(data, index=dates, columns=field_names)

    def _parse_data_row(self, row, relevant_fields_indices, idx_of_date_column):
        td_elems = row.findAll('td')

        rows_date = None
        numeric_values = []

        for i, elem in enumerate(td_elems):
            if i not in relevant_fields_indices:
                continue
            elif i == idx_of_date_column:
                parsed_date = datetime.strptime(elem.string, '%b %d, %Y')
                rows_date = parsed_date
            else:
                value = self._parse_numeric_value(elem.string)
                numeric_values.append(value)

        return rows_date, numeric_values

    @classmethod
    def _parse_numeric_value(cls, value: str) -> Optional[float]:
        if value == '-':
            value = None
        else:
            try:
                value = float((value.replace(',', '')))
            except ValueError:
                value = None

        return value

    @staticmethod
    def _format_single_ticker_table(table: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # create index from column and remove redundant info
        table.set_index(keys='date', inplace=True)
        table = table.drop('ticker', axis=1)

        # cut the dates if necessary
        table = table.loc[start_date:end_date]

        return table
