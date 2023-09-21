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
from datetime import datetime
from itertools import islice


def get_formatted_filename(reports_title, date: datetime, extension: str):
    str_date = date.strftime("%Y_%m_%d-%H%M")
    filename = "{str_date:s} {reports_title:s}.{extension:s}".format(str_date=str_date, reports_title=reports_title,
                                                                     extension=extension)
    # replace spaces with underscore
    filename = filename.replace(" ", "_")

    return filename


def grouper(chunk_size: int, iterable):
    """
    Group an iterable into n-sized chunks

    Parameters
    ----------
    chunk_size
        the size of the chunk
    iterable
    """
    it = iter(iterable)
    while True:
        batch = list(islice(it, chunk_size))
        if not batch:
            break
        yield batch
