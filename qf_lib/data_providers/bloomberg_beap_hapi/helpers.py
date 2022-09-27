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
from typing import List

from numpy import float64
from pandas import to_datetime, notna
from pandas._libs.tslibs.nattype import NaT

from qf_lib.containers.series.qf_series import QFSeries


class BloombergDataLicenseTypeConverter:

    def infer_type(self, series: QFSeries, bbg_data_type: str) -> QFSeries:
        field_types = {
            "String": self._string_conversion,
            "Character": self._string_conversion,
            "Long Character": self._string_conversion,
            "Date or Time": self._date_conversion,
            "Integer": self._float_conversion,  # To support NaN values all Integers are mapped to floats
            "Integer/Real": self._float_conversion,
            "Date": self._date_conversion,
            "Real": self._float_conversion,
            "Month/Year": self._string_conversion,
            "Price": self._float_conversion,
            "Bulk Format": self._bulk_conversion
        }

        _conversion_fun = field_types.get(bbg_data_type, id)
        return _conversion_fun(series)

    @staticmethod
    def _date_conversion(series: QFSeries) -> QFSeries:
        return to_datetime(series, format="%Y%m%d", errors='coerce').replace({NaT: None})

    @staticmethod
    def _string_conversion(series: QFSeries) -> QFSeries:
        return series.apply(lambda s: s.strip() if notna(s) else None).replace({"N.A.": None})

    @staticmethod
    def _float_conversion(series: QFSeries) -> QFSeries:
        return series.replace({"N.A.": None}).astype(float64)

    @staticmethod
    def _bulk_conversion(series: QFSeries) -> QFSeries:
        def _split_bulk_list(_l: List):
            _char = ';4;'  # String representing new bulk element
            return _l[_l.find(_char) + len(_char):].rstrip(';').split(_char) if len(_l) > 0 else []
        return series.fillna("").apply(_split_bulk_list)
