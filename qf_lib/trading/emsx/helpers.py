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
from blpapi import Session, Identity
from qf_lib.backtesting.order.execution_style import ExecutionStyle, MarketOrder, MarketOnCloseOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.data_providers.bloomberg.helpers import get_response_events
from qf_lib.trading.emsx.names import AUTHORIZATION_SERVICE, AUTHORIZATION_SUCCESS, AUTHORIZATION_FAILURE


def initialize_session(host: str, port: int):
    """ Initializes Bloomberg API session and returns the corresponding Session object. """
    session_options = blpapi.SessionOptions()
    session_options.setServerHost(host)
    session_options.setServerPort(port)
    session_options.setAutoRestartOnDisconnection(True)

    return blpapi.Session(session_options)


def authorize_emsx_user(session: Session, host: str, username: str) -> Identity:
    """ Given session, name of the host and the username, opens the authorization service and sends an
    authorization request to create identity for the user.

    Returns
    --------
    Identity
        if the authorization is successful, the function returns the created Identity for the user

    Raises
    -------
    ConnectionError
        in case if the authorization is unsuccessful or the connection was not properly established
    """
    if not session.openService(AUTHORIZATION_SERVICE):
        raise ConnectionError(f"Failed to open service: {AUTHORIZATION_SERVICE}")

    auth_service = session.getService(AUTHORIZATION_SERVICE)
    auth_request = auth_service.createAuthorizationRequest()
    auth_request.set("emrsId", username)
    auth_request.set("ipAddress", host)

    identity = session.createIdentity()

    session.sendAuthorizationRequest(auth_request, identity)

    response_events = get_response_events(session)
    for event in response_events:
        for msg in event:
            if msg.messageType() == AUTHORIZATION_SUCCESS:
                return identity
            elif msg.messageType() == AUTHORIZATION_FAILURE:
                raise ConnectionError(f"Authorization failed for user {username}.")

    raise ConnectionError("No authorization acknowledgment received.")


def execution_style_to_bbg_map(execution_style: ExecutionStyle) -> str:
    """ For a given order execution_style returns the corresponding string field (e.g. MKT for Market Order).
    Order types supported by EMSX: CD, FUN, LMT, LOC, MKT, MOC, OC, SL, ST, PEG
    """
    execution_style_to_str = {
        MarketOrder: "MKT",
        MarketOnCloseOrder: "MOC",
    }

    try:
        return execution_style_to_str[type(execution_style)]
    except KeyError:
        raise NotImplementedError("The given execution_style: {} is not supported.".format(type(execution_style)))


def emsx_order_type_to_execution_style(order_type: str) -> ExecutionStyle:
    order_type_to_execution_style = {
        "MKT": MarketOrder(),
        "MOC": MarketOnCloseOrder(),
    }
    try:
        return order_type_to_execution_style[order_type]
    except KeyError:
        raise NotImplementedError("The given order type: {} is not supported.".format(order_type))


def time_in_force_to_bbg_map(time_in_force: TimeInForce):
    time_in_force_to_str = {
        TimeInForce.GTC: "GTC",
        TimeInForce.DAY: "DAY",
        TimeInForce.OPG: "OPG"
    }

    try:
        return time_in_force_to_str[time_in_force]
    except KeyError:
        raise NotImplementedError("The given time_in_force: {} is not supported.".format(time_in_force.name))


def emsx_tif_to_time_in_force(tif: str):
    time_in_force_to_str = {
        "GTC": TimeInForce.GTC,
        "DAY": TimeInForce.DAY,
        "OPG": TimeInForce.OPG
    }
    try:
        return time_in_force_to_str[tif]
    except KeyError:
        raise NotImplementedError("The given time_in_force: {} is not supported.".format(tif))
