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
import gzip
import re
from io import StringIO
from typing import Tuple, List, Optional, Dict
from pandas import to_datetime
from pandas._libs.tslibs.nattype import NaT
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.helpers import tickers_dict_to_data_array
import numpy as np
import csv


class BloombergBeapHapiParser:
    """
    Class to parse responses from BEAP HAPI

    Format of the response file:

    START-OF-FILE

    # Required headers
    HEADER_KEY_1=header_value_1

    START-OF-FIELDS
    FIELD
    END-OF-FIELDS

    TIMESTARTED=Mon Jan 01 00:00:00 GMT 2020
    START-OF-DATA
    X|X|X|
    END-OF-DATA
    TIMEFINISHED=Mon Jan 01 00:00:00 GMT 2020

    END-OF-FILE
    """

    def __init__(self):
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_chain(self, filepath: str) -> Dict[str, List[str]]:
        """
        Method to parse hapi response and extract future chain tickers

        Parameters
        ----------
        filepath: str
            The full filepath with downloaded response

        Returns
        -------
        data: Dict
            Dictionary with data, in the format [str] -> List[str]
            where the key - active future ticker (str), values - tickers from chain
        """
        _, content = self._get_fields_and_data_content(filepath, column_names=["Active ticker"])

        content = content.set_index('Active ticker')
        active_tickers = content.index.unique()
        content = content.squeeze()

        data = {
            active_ticker: content.loc[active_ticker].values.tolist() for active_ticker in active_tickers
        }

        return data

    def get_current_values_dates_fields_format(self, filepath: str) -> QFDataFrame:
        """
        Method to parse hapi response and extract dates (e.g. FUT_NOTICE_FIRST, LAST_TRADEABLE_DT) for tickers

        Parameters
        ----------
        filepath: str
            The full filepath with downloaded response

        Returns
        -------
        df: QFDataFrame
            df with data
            # e.g. index: C U59 Comdty, C Z59 Comdty, C H60 Comdty, C K60 Comdty
            # e.g. columns: FUT_NOTICE_FIRST, LAST_TRADEABLE_DT
        """
        fields, content = self._get_fields_and_data_content(filepath, column_names=["Ticker", "Error code", "Num flds"],
                                                            replace_header=True)

        content = content.set_index("Ticker")
        content = content.drop(columns=["Error code", "Num flds"])
        for field in fields:
            content[field] = to_datetime(content[field], format="%Y%m%d", errors="coerce")

        # Replace NaT with None
        content = content.replace({NaT: None})
        return content

    def get_history(self, filepath: str) -> QFDataArray:
        """
        Method to parse hapi response and get history data

        Parameters
        ----------
        filepath: str
            The full filepath with downloaded response

        Returns
        -------
        QFDataArray
            QFDataArray with history data
        """
        fields, content = self._get_fields_and_data_content(filepath, column_names=["Ticker", "Error code", "Num flds",
                                                                                    "Pricing Source", "Dates"])
        tickers = content["Ticker"].unique().tolist()
        content["Dates"] = to_datetime(content["Dates"], format="%Y%m%d")
        content = content.drop(columns=["Error code", "Num flds", "Pricing Source"])

        def extract_tickers_df(data_array, ticker: str):
            df = data_array[data_array["Ticker"] == ticker].drop(columns="Ticker")
            df = df.dropna(subset=["Dates"]).set_index("Dates")
            return df

        tickers_dict = {
            t: extract_tickers_df(content, t) for t in tickers
        }

        return tickers_dict_to_data_array(tickers_dict, tickers, fields)

    def _get_fields_and_data_content(self, filepath: str, column_names: Optional[List] = None,
                                     replace_header: bool = False, expect_data_array: bool = False) -> Tuple:
        """
        Helper function to extract fields and content of the hapi response between following (including headers):
        fields: START-OF-FIELDS - END-OF-FIELDS
        content: START-OF-DATA - END-OF-DATA

        Parameters
        ----------
        filepath: str
            The full filepath with downloaded response
        column_names: List[str]
            list of names to be used as column names of the dataframe
        replace_header: bool
            if True - the data already contains a header and it should be replaced with the given column names,
            if False - it is assumed that data does not have any header

        Returns
        -------
        fields, content: Tuple[List[str], QFDataFrame]
            Extracted fields and content from the response, each item in the list represent one value
            Fields contains all fields
            Content contains the list of all rows separated by "|", which need to be proceed further
        """
        f = gzip.open(filepath, 'rb')
        data = f.read().decode("utf-8")
        # Without re.DOTALL, each line of the input text matches the pattern separately
        fields = re.search(r'START-OF-FIELDS\n(.*?)\nEND-OF-FIELDS', data, re.DOTALL).group(1).split('\n')
        content = re.search(r'START-OF-DATA\n(.*?)\nEND-OF-DATA', data, re.DOTALL).group(1)

        column_names = column_names + fields if column_names is not None else None
        content = self._read_csv(content, column_names, replace_header)

        content = content.replace(r'^\s+$', np.nan, regex=True)
        str_columns = content.select_dtypes(['object']).columns
        content.loc[:, str_columns] = content.loc[:, str_columns].apply(lambda x: x.str.strip())
        content = QFDataFrame(content)

        return fields, content

    def _read_csv(self, content: str, column_names: List[str], replace_header: bool, delimiter: str = "|"):
        # Remove trailing delimiters
        content = "\n".join(line.rstrip("|") for line in content.split("\n"))
        lines = csv.reader(StringIO(content), delimiter=delimiter)
        records = list(lines) if not replace_header else list(lines)[1:]
        records = [line for line in records if len(line) == len(column_names)]
        df = QFDataFrame.from_records(records, columns=column_names)
        return df
