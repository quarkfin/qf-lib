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
from typing import Dict

import numpy as np
from pandas import read_json, DataFrame, Series, to_datetime, NaT, notna

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray


class BloombergDLParser:

    def __init__(self):
        self._TYPE_TO_CAST_FUNCTION = {
            "String": self._string_conversion,
            "Character": self._string_conversion,
            "Long Character": self._string_conversion,
            "Date or Time": self._date_conversion,
            "Time": self._time_conversion,
            "Integer": self._float_conversion,  # To support NaN values all Integers are mapped to floats
            "Integer/Real": self._float_conversion,
            "Date": self._date_conversion,
            "Real": self._float_conversion,
            "Month/Year": self._string_conversion,
            "Price": self._float_conversion,
            "Bulk Format": self._bulk_conversion
        }

    @staticmethod
    def decompress_response(raw_bytes: bytes) -> DataFrame:
        try:
            data = gzip.decompress(raw_bytes)
        except (gzip.BadGzipFile, OSError):
            data = raw_bytes

        return read_json(data.decode("utf-8"))

    def get_current_values(self, data_frame, field_mapping: Dict) -> QFDataFrame:
        data_frame = data_frame.set_index(["IDENTIFIER"])[[*field_mapping.keys()]]
        data_frame.index = data_frame.index.rename("tickers")

        for column, group in field_mapping.items():
            data_frame[column] = self._TYPE_TO_CAST_FUNCTION[group](data_frame[column])

        return data_frame

    def get_history(self, data_frame, field_mapping: Dict) -> QFDataArray:
        data_frame["DATE"] = to_datetime(data_frame["DATE"])
        data_frame = data_frame.dropna(subset=["DATE", "IDENTIFIER"])
        data_frame = data_frame.set_index(["DATE", "IDENTIFIER"])[[*field_mapping.keys()]]

        for column, group in field_mapping.items():
            data_frame[column] = self._TYPE_TO_CAST_FUNCTION[group](data_frame[column])

        fetched_dates = data_frame.index.unique(level=0).values
        fetched_fields = data_frame.columns
        fetched_tickers = data_frame.index.unique(level=1).values

        data_reshaped = np.reshape(data_frame.values, (len(fetched_dates), len(fetched_tickers), len(fetched_fields)))
        data_array = QFDataArray.create(fetched_dates, fetched_tickers, fetched_fields, data_reshaped)
        return data_array

    @staticmethod
    def _date_conversion(series: Series) -> Series:
        return to_datetime(series, format="%Y-%m-%d", errors='coerce').replace({NaT: None})

    @staticmethod
    def _time_conversion(series: Series) -> Series:
        return to_datetime(series, errors='coerce').dt.time.replace({NaT: None})

    @staticmethod
    def _string_conversion(series: Series) -> Series:
        return series.apply(lambda s: s.strip() if notna(s) else None).replace({"N.A.": None})

    @staticmethod
    def _float_conversion(series: Series) -> Series:
        return series.replace({"N.A.": None}).astype(np.float64)

    @staticmethod
    def _bulk_conversion(series: Series) -> Series:
        return series.fillna("")
