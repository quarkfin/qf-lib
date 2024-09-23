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

"""
This module offers a comprehensive set of containers for financial data analysis, including series, dataframes, data arrays, and futures-related objects.

Each container type is designed with specialized classes to handle various aspects of financial data, such as price series, return calculations, and futures contract management.
These classes streamline the processing and analysis of complex financial datasets, providing a robust framework for quantitative finance research.

Notes:
  - When constructing a container object, the input data is typically expected to be in a wide format. For example:
    - A `PricesSeries` object might be initialized with a DataFrame where each column represents the price history of a different asset.
    - A `QFDataArray` can be created using multi-dimensional arrays to represent time, asset, and other axes of data.

"""
