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

GET_FILLS_RESPONSE = blpapi.Name("GetFillsResponse")
ERROR_INFO = blpapi.Name("ErrorInfo")

AUTHORIZATION_SERVICE = "//blp/apiauth"
AUTHORIZATION_SUCCESS = blpapi.Name("AuthorizationSuccess")
AUTHORIZATION_FAILURE = blpapi.Name("AuthorizationFailure")

CREATE_ORDER_AND_ROUTE_EX = blpapi.Name("CreateOrderAndRouteEx")
CREATE_ORDER = blpapi.Name("CreateOrder")
CANCEL_ORDER = blpapi.Name("CancelOrderEx")

HISTORY_SERVICE_DEMO = "//blp/emsx.history.uat"
HISTORY_SERVICE = "//blp/emsx.history"

EMSX_SERVICE_DEMO = "//blp/emapisvc_beta"
EMSX_SERVICE = "//blp/emapisvc"
