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
from typing import Tuple, List, Dict

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.bloomberg_beap_hapi.helpers import BloombergDataLicenseTypeConverter
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
        self.type_converter = BloombergDataLicenseTypeConverter()

    def get_current_values(self, filepath: str, field_to_type: Dict[str, str]) -> QFDataFrame:
        """
        Method to parse hapi response and extract dates (e.g. FUT_NOTICE_FIRST, LAST_TRADEABLE_DT) for tickers

        Parameters
        ----------
        filepath: str
            The full filepath with downloaded response
        field_to_type: Dict[str, str]
            dictionary mapping requested, correct fields into their corresponding types

        Returns
        -------
        QFDataFrame
            QFDataFrame with current values
        """
        column_names = ["Ticker", "Error code", "Num flds"]
        field_to_type = {**field_to_type, "Ticker": "String"}
        fields, content = self._get_fields_and_data_content(filepath, field_to_type, column_names, header_row=True)

        return content.set_index("Ticker")[fields]

    def get_history(self, filepath: str, field_to_type: Dict[str, str], tickers_mapping: Dict[str, BloombergTicker]) \
            -> QFDataArray:
        """
        Method to parse hapi response and get history data

        Parameters
        ----------
        filepath: str
            The full filepath with downloaded response
        field_to_type: Dict[str, str]
            dictionary mapping requested, correct fields into their corresponding types
        tickers_mapping: Dict[str, BloombergTicker]
            dictionary mapping string representations of tickers onto corresponding ticker objects

        Returns
        -------
        QFDataArray
            QFDataArray with history data
        """
        column_names = ["Ticker", "Error code", "Num flds", "Pricing Source", "Dates"]
        field_to_type = {**field_to_type, "Ticker": "String", "Error code": "String", "Num flds": "String",
                         "Pricing Source": "String", "Dates": "Date"}
        fields, content = self._get_fields_and_data_content(filepath, field_to_type, column_names)

        tickers_dict = {
            tickers_mapping[ticker]: df.set_index("Dates")[fields].dropna(how="all")
            for ticker, df in content.groupby(by="Ticker")
        }

        return tickers_dict_to_data_array(tickers_dict, list(tickers_dict.keys()), fields)

    def _get_fields_and_data_content(self, filepath: str, field_to_type: Dict, column_names: List,
                                     header_row: bool = False) -> Tuple[List, QFDataFrame]:
        """
        Helper function to extract fields and content of the hapi response between following (including headers):
        fields: START-OF-FIELDS - END-OF-FIELDS
        content: START-OF-DATA - END-OF-DATA

        Parameters
        ----------
        filepath: str
            The full filepath with downloaded response
        field_to_type: Dict[str, str]
            dictionary mapping requested, correct fields into their corresponding types
        column_names: List[str]
            list of names to be used as column names of the dataframe
        header_row: bool
            indicated whether header is present in the response file (current values response) or not (historical
            data response)

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
        content = self._read_csv(content, column_names + fields, header_row=header_row)

        for col, _type in field_to_type.items():
            content.loc[:, col] = self.type_converter.infer_type(content.loc[:, col], _type)

        return fields, content

    @staticmethod
    def _read_csv(content: str, column_names: List[str], delimiter: str = "|", header_row: bool = False):
        # Remove trailing delimiters
        content = "\n".join(line.rstrip("|") for line in content.split("\n"))
        lines = csv.reader(StringIO(content), delimiter=delimiter)
        records = list(lines) if not header_row else list(lines)[1:]
        records = [line for line in records if len(line) == len(column_names)]
        df = QFDataFrame.from_records(records, columns=column_names)
        return df.replace(r'^\s+$', np.nan, regex=True)
