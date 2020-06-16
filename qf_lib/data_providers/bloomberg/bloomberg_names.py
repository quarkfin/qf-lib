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

import blpapi

DATE = blpapi.Name("date")
ERROR_INFO = blpapi.Name("errorInfo")
EVENT_TIME = blpapi.Name("EVENT_TIME")
FIELDS = blpapi.Name("fields")
FIELD_DATA = blpapi.Name("fieldData")
FIELD_EXCEPTIONS = blpapi.Name("fieldExceptions")
FIELD_ID = blpapi.Name("fieldId")
SECURITY = blpapi.Name("security")
SECURITIES = blpapi.Name("securities")
SECURITY_DATA = blpapi.Name("securityData")
RESPONSE_ERROR = blpapi.Name("responseError")
SECURITY_ERROR = blpapi.Name("securityError")
CURRENCY = blpapi.Name("currency")

START_DATE = blpapi.Name("startDate")
END_DATE = blpapi.Name("endDate")
PERIODICITY_SELECTION = blpapi.Name("periodicitySelection")
PERIODICITY_ADJUSTMENT = blpapi.Name("periodicityAdjustment")

TIME = blpapi.Name("time")
START_DATE_TIME = blpapi.Name("startDateTime")
END_DATE_TIME = blpapi.Name("endDateTime")
INTERVAL = blpapi.Name("interval")
BAR_DATA = blpapi.Name("barData")
BAR_TICK_DATA = blpapi.Name("barTickData")

OPEN = blpapi.Name("open")
CLOSE = blpapi.Name("close")
LOW = blpapi.Name("low")
HIGH = blpapi.Name("high")
VOLUME = blpapi.Name("volume")

REF_DATA_SERVICE_URI = "//blp/refdata"  # address of bloomberg service

FUT_CHAIN = blpapi.Name("FUT_CHAIN")
