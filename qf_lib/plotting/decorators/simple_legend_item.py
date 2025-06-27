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
from typing import Optional


class SimpleLegendItem:
    """
    An item which can be added to a Legend in a simple way: by using its handle property. Handle is a reference
    to the matplotlib.Artist object.

    Object which holds a reference to matplotlib's object which can be plotted on the chart (so called Artist).
    """

    def __init__(self, legend_artist: Optional = None) -> None:

        self.legend_artist = legend_artist  # type: matplotlib.artist.Artist
