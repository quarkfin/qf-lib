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

class BrokerException(Exception):
    """
    Exception thrown when a Broker's operation fails.
    """
    pass


class OrderCancellingException(BrokerException):
    """
    Order couldn't be cancelled (e.g. because there was no Order of that id in the list of awaiting Orders
    or the request to cancel it timed-out).
    """
    pass
