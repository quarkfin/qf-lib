import logging
from datetime import date, datetime
from typing import Dict, Optional, Sequence, Union

import pandas as pd
from bs4 import BeautifulSoup as BS
from bs4 import Tag
from requests import Session

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import CcyTicker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider


class CryptoCurrencyDataProvider(AbstractPriceDataProvider):
    """
    Constructs a new ``CryptoCurrencyDataProvider`` instance
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.earliest_api_date = "20130428"

    def get_history(self, tickers: Union[CcyTicker, Sequence[CcyTicker]],
                    fields: Union[None, str, Sequence[str]] = None,
                    start_date: datetime = None, end_date: datetime = None, **kwargs) \
            -> Union[QFSeries, QFDataFrame, pd.Panel]:
        """
        When fields is None, all available fields will be returned
        """
        tickers, got_single_ticker = convert_to_list(tickers, CcyTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        result_dict = dict()
        with Session() as session:
            for ticker in tickers:
                result_dict[ticker] = self._get_single_ticker(
                    ticker, fields, start_date, end_date, session)

        panel = self._dict_to_panel_or_df(result_dict, tickers, fields)
        got_single_date = self._is_single_date(start_date, end_date)
        result = self._squeeze_panel(
            panel, got_single_date, got_single_ticker, got_single_field)
        result = self._cast_result_to_proper_type(result)
        result = result.sort_index()
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
        end_date = end_date.strftime("%Y%m%d")

        if start_date is not None:
            start_date = start_date.strftime("%Y%m%d")
            if start_date < self.earliest_api_date:
                self.logger.warning(
                    "This date is earlier than the earliest records on the API. Using the earliest possible date "
                    "instead (2013-04-28)"
                )
        else:
            start_date = self.earliest_api_date

        request = session.get("http://coinmarketcap.com/currencies/" +
                              ticker.as_string() + "/historical-data/?start=" + start_date + "&end=" + end_date)

        if request.status_code is not 200:
            if request.status_code == 404:
                self.logger.error(
                    "The ticker {} does not exist on the API".format(ticker.as_string()))
            else:
                raise ConnectionError(
                    "Something went wrong connecting to the API. Try again later."
                )
            return

        table = BS(request.content, 'lxml').table

        if table is None:
            raise AttributeError(
                "No data was found for the ticker. This could be an error on the API, or they may have changed their "
                "layout format."
            )

        headersHTML = table.findAll('th')
        headers = list()
        for headerHTML in headersHTML:
            headers.append(headerHTML.string)

        dates = list()
        data = list()

        rows = table.findAll('tr')
        for row in rows[1:]:
            value_dict = self._parse_values(
                row.findAll('td'), headers, fields=fields)
            dates.append(value_dict['Date'])
            del value_dict['Date']
            data.append(value_dict)

        return pd.DataFrame(data, dates)

    @classmethod
    def _parse_values(cls, values: Sequence[Tag], headers: Sequence[str], fields: Sequence[str] = None):
        """
        Parses the value from a string to the correct type and filters the values to those requested
        """
        result = dict()
        for index, value in enumerate(values):
            if index == 0:
                value = datetime.strptime(value.string, '%b %d, %Y')
            else:
                if value != '-':
                    try:
                        value = float((value.string.replace(',', '')))
                    except ValueError:
                        value = None
                else:
                    value = None

            for field in fields:
                if headers[index] == field or headers[index] == 'Date':
                    result[headers[index]] = value

        return result

    @staticmethod
    def _format_single_ticker_table(table: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # create index from column and remove redundant info
        table.set_index(keys='date', inplace=True)
        table = table.drop('ticker', axis=1)

        # cut the dates if necessary
        table = table.loc[start_date:end_date]

        return table

    @staticmethod
    def _dict_to_panel_or_df(tickers_to_data_dict: dict, tickers: Sequence[CcyTicker], fields) -> pd.Panel:
        """
        Converts a dictionary tickers->DateFrame to Panel.

        Parameters
        ----------
        tickers_to_data_dict: dict[str, pd.DataFrame]

        Returns
        -------
        pandas.Panel  [date, ticker, field] or
        QFDataFrame [date, tickers] if single field was provided

        """
        panel = pd.Panel.from_dict(data=tickers_to_data_dict)

        # recombines dimensions, so that the first one is date, major is ticker, minor is field
        panel = panel.transpose(1, 0, 2)

        # to keep the order of tickers and fields we reindex the panel
        if fields is not None:
            # to handle single and many fields.
            fields = pd.np.array(fields, ndmin=1)
            panel = panel.reindex(major_axis=tickers, minor_axis=fields)
        else:
            panel = panel.reindex(major_axis=tickers)

        return panel
