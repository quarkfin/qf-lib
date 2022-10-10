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

EMSX_SUBSCRIPTION_BETA = """<?xml version="1.0" encoding="UTF-8" ?>
<ServiceDefinition xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    name="emapisvc_beta" version="3.33.1.8">
    <service name="//blp/emapisvc_beta" version="3.33.1.8">
        <operation name="CreateOrder" serviceId="14873">
            <request>Request</request>
            <requestSelection>CreateOrder</requestSelection>
            <response>Response</response>
            <responseSelection>CreateOrder</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="CreateOrderAndRoute" serviceId="14873">
            <request>Request</request>
            <requestSelection>CreateOrderAndRoute</requestSelection>
            <response>Response</response>
            <responseSelection>CreateOrderAndRoute</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="CreateOrderAndRouteManually" serviceId="14873">
            <request>Request</request>
            <requestSelection>CreateOrderAndRouteManually</requestSelection>
            <response>Response</response>
            <responseSelection>CreateOrderAndRouteManually</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="ModifyOrder" serviceId="14873">
            <request>Request</request>
            <requestSelection>ModifyOrder</requestSelection>
            <response>Response</response>
            <responseSelection>ModifyOrder</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="DeleteOrder" serviceId="14873">
            <request>Request</request>
            <requestSelection>DeleteOrder</requestSelection>
            <response>Response</response>
            <responseSelection>DeleteOrder</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="OrderInfo" serviceId="14873">
            <request>Request</request>
            <requestSelection>OrderInfo</requestSelection>
            <response>Response</response>
            <responseSelection>OrderInfo</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="RouteInfo" serviceId="14873">
            <request>Request</request>
            <requestSelection>RouteInfo</requestSelection>
            <response>Response</response>
            <responseSelection>RouteInfo</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="Route" serviceId="14873">
            <request>Request</request>
            <requestSelection>Route</requestSelection>
            <response>Response</response>
            <responseSelection>Route</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="RouteManually" serviceId="14873">
            <request>Request</request>
            <requestSelection>RouteManually</requestSelection>
            <response>Response</response>
            <responseSelection>RouteManually</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="ModifyRoute" serviceId="14873">
            <request>Request</request>
            <requestSelection>ModifyRoute</requestSelection>
            <response>Response</response>
            <responseSelection>ModifyRoute</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="CancelRoute" serviceId="14873">
            <request>Request</request>
            <requestSelection>CancelRoute</requestSelection>
            <response>Response</response>
            <responseSelection>CancelRoute</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="CancelRouteEx" serviceId="14873">
            <request>Request</request>
            <requestSelection>CancelRouteEx</requestSelection>
            <response>Response</response>
            <responseSelection>CancelRouteEx</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetTeams" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetTeams</requestSelection>
            <response>Response</response>
            <responseSelection>GetTeams</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetFieldMetaData" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetFieldMetaData</requestSelection>
            <response>Response</response>
            <responseSelection>GetFieldMetaData</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetAllFieldMetaData" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetAllFieldMetaData</requestSelection>
            <response>Response</response>
            <responseSelection>GetAllFieldMetaData</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetAssetClass" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetAssetClass</requestSelection>
            <response>Response</response>
            <responseSelection>GetAssetClass</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetBrokersWithAssetClass" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetBrokersWithAssetClass</requestSelection>
            <response>Response</response>
            <responseSelection>GetBrokersWithAssetClass</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetBrokerStrategiesWithAssetClass" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetBrokerStrategiesWithAssetClass</requestSelection>
            <response>Response</response>
            <responseSelection>GetBrokerStrategiesWithAssetClass</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetBrokerStrategyInfoWithAssetClass"
            serviceId="14873">
            <request>Request</request>
            <requestSelection>GetBrokerStrategyInfoWithAssetClass</requestSelection>
            <response>Response</response>
            <responseSelection>GetBrokerStrategyInfoWithAssetClass</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetBrokers" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetBrokers</requestSelection>
            <response>Response</response>
            <responseSelection>GetBrokers</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetBrokerStrategies" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetBrokerStrategies</requestSelection>
            <response>Response</response>
            <responseSelection>GetBrokerStrategies</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetBrokerStrategyInfo" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetBrokerStrategyInfo</requestSelection>
            <response>Response</response>
            <responseSelection>GetBrokerStrategyInfo</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="CreateOrderAndRouteWithStrat" serviceId="14873">
            <request>Request</request>
            <requestSelection>CreateOrderAndRouteWithStrat</requestSelection>
            <response>Response</response>
            <responseSelection>CreateOrderAndRouteWithStrat</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="RouteWithStrat" serviceId="14873">
            <request>Request</request>
            <requestSelection>RouteWithStrat</requestSelection>
            <response>Response</response>
            <responseSelection>RouteWithStrat</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="ModifyRouteWithStrat" serviceId="14873">
            <request>Request</request>
            <requestSelection>ModifyRouteWithStrat</requestSelection>
            <response>Response</response>
            <responseSelection>ModifyRouteWithStrat</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GroupRouteWithStrat" serviceId="14873">
            <request>Request</request>
            <requestSelection>GroupRouteWithStrat</requestSelection>
            <response>Response</response>
            <responseSelection>GroupRouteWithStrat</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="RouteEx" serviceId="14873">
            <request>Request</request>
            <requestSelection>RouteEx</requestSelection>
            <response>Response</response>
            <responseSelection>Route</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="ModifyRouteEx" serviceId="14873">
            <request>Request</request>
            <requestSelection>ModifyRouteEx</requestSelection>
            <response>Response</response>
            <responseSelection>ModifyRouteEx</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GroupRouteEx" serviceId="14873">
            <request>Request</request>
            <requestSelection>GroupRouteEx</requestSelection>
            <response>Response</response>
            <responseSelection>GroupRouteEx</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="CreateOrderAndRouteEx" serviceId="14873">
            <request>Request</request>
            <requestSelection>CreateOrderAndRouteEx</requestSelection>
            <response>Response</response>
            <responseSelection>CreateOrderAndRouteEx</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="RouteManuallyEx" serviceId="14873">
            <request>Request</request>
            <requestSelection>RouteManuallyEx</requestSelection>
            <response>Response</response>
            <responseSelection>RouteManually</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="AssignTrader" serviceId="14873">
            <request>Request</request>
            <requestSelection>AssignTrader</requestSelection>
            <response>Response</response>
            <responseSelection>AssignTrader</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="SellSideAck" serviceId="14873">
            <request>Request</request>
            <requestSelection>SellSideAck</requestSelection>
            <response>Response</response>
            <responseSelection>SellSideAck</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="SellSideReject" serviceId="14873">
            <request>Request</request>
            <requestSelection>SellSideReject</requestSelection>
            <response>Response</response>
            <responseSelection>SellSideReject</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="CancelOrderEx" serviceId="14873">
            <request>Request</request>
            <requestSelection>CancelOrderEx</requestSelection>
            <response>Response</response>
            <responseSelection>CancelOrderEx</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="ModifyOrderEx" serviceId="14873">
            <request>Request</request>
            <requestSelection>ModifyOrderEx</requestSelection>
            <response>Response</response>
            <responseSelection>ModifyOrderEx</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="ManualFill" serviceId="14873">
            <request>Request</request>
            <requestSelection>ManualFill</requestSelection>
            <response>Response</response>
            <responseSelection>ManualFill</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetTraders" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetTraders</requestSelection>
            <response>Response</response>
            <responseSelection>GetTraders</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="GetTradeDesks" serviceId="14873">
            <request>Request</request>
            <requestSelection>GetTradeDesks</requestSelection>
            <response>Response</response>
            <responseSelection>GetTradeDesks</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <operation name="CreateBasket" serviceId="14873">
            <request>Request</request>
            <requestSelection>CreateBasket</requestSelection>
            <response>Response</response>
            <responseSelection>CreateBasket</responseSelection>
            <responseSelection>ErrorInfo</responseSelection>
        </operation>
        <event name="OrderRouteFields" eventType="OrderRouteFields">
            <eventId>1</eventId>
            <cacheable>true</cacheable>
        </event>
        <defaultServiceId>196982</defaultServiceId>
        <publisherSupportsRecap>false</publisherSupportsRecap>
        <authoritativeSourceSupportsRecap>false</authoritativeSourceSupportsRecap>
        <SubscriberResolutionServiceId>15385</SubscriberResolutionServiceId>
        <isInfrastructureService>false</isInfrastructureService>
        <isMetered>false</isMetered>
        <appendMtrId>false</appendMtrId>
        <persistentLastValueCache>false</persistentLastValueCache>
    </service>
    <schema name="emapisvc_beta" version="3.33.1.8">
        <sequenceType name="FieldData">
            <description></description>
            <element name="EMSX_FIELD_DATA" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="FieldIndicator">
            <description></description>
            <element name="EMSX_FIELD_INDICATOR" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="Strategy">
            <description></description>
            <element name="EMSX_STRATEGY_NAME" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_FIELDS" type="FieldData"
                minOccurs="1" maxOccurs="20">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_FIELD_INDICATORS"
                type="FieldIndicator" minOccurs="1" maxOccurs="20">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="StrategyInfoDetails">
            <description></description>
            <element name="FieldName" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Disable" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="StringValue" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="SpreadFields">
            <description></description>
        </sequenceType>
        <sequenceType name="MultilegFields">
            <description></description>
            <element name="EMSX_ML_RATIO" type="Int32" minOccurs="1"
                maxOccurs="5">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="MultilegID">
            <description></description>
            <element name="EMSX_ML_ID" type="String" minOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="FieldMetaData">
            <description></description>
            <element name="EMSX_FIELD_NAME" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_DISP_NAME" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TYPE" type="FieldTypeEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEVEL" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEN" type="Int32" minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="RouteRefIDs">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_REF_ID" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetTradersRequest">
            <description></description>
        </sequenceType>
        <sequenceType name="GetTradeDesksRequest">
            <description></description>
            <element name="Scope" type="IdentityType" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetTradersResponse">
            <description></description>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetTradeDesksResponse">
            <description></description>
            <element name="EMSX_TRADE_DESK" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CreateOrderRequest">
            <description></description>
            <element name="EMSX_SIDE" type="SideEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE_DESTINATION" type="String"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_ORIGIN" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RESERVED_FIELD1" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BASKET_NAME" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_REF_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_INVESTOR_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE1" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE2" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE3" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE4" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE5" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_TYPE" type="SettleTypeEnum"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_CURRENCY" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BUYSIDE_LEI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLIENT_IDENTIFICATION"
                type="MifidClientIdentification" minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SI" type="MifidIsSi" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_MIFID_II_INSTRUCTION"
                type="MifidTradingInsructionEnum" minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GPI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AS_OF_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AS_OF_TIME_MICROSEC" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CreateOrderAndRouteRequest">
            <description></description>
            <element name="EMSX_SIDE" type="SideEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE_DESTINATION" type="String"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_ORIGIN" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RESERVED_FIELD1" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RESERVED_FIELD2" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_REF_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_INVESTOR_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CreateOrderAndRouteRequestEx">
            <description></description>
            <element name="EMSX_SIDE" type="SideEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE_DESTINATION" type="String"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_ORIGIN" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_REF_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_INVESTOR_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE1" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE2" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE3" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE4" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE5" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_TYPE" type="SettleTypeEnum"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_CURRENCY" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_REF_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BOOKNAME" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BUYSIDE_LEI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLIENT_IDENTIFICATION"
                type="MifidClientIdentification" minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SI" type="MifidIsSi" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_MIFID_II_INSTRUCTION"
                type="MifidTradingInsructionEnum" minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GPI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AS_OF_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AS_OF_TIME_MICROSEC" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TOMS_PXNUM" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CreateOrderWithStratRequest">
            <description></description>
            <element name="EMSX_SIDE" type="SideEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE_DESTINATION" type="String"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_ORIGIN" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_REF_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_INVESTOR_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE1" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE2" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE3" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE4" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE5" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_TYPE" type="SettleTypeEnum"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_CURRENCY" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="RouteOrderRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="RouteOrderWithStratRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="RouteOrderRequestEx">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_REF_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BOOKNAME" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_MIFID_II_INSTRUCTION"
                type="MifidTradingInsructionEnum" minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GPI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AS_OF_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AS_OF_TIME_MICROSEC" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TOMS_PXNUM" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GroupRouteWithStratRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="3000">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT_PERCENT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GroupRouteRequestEx">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="3000">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT_PERCENT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_RELEASE_TIME" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOCATE_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_TYPE" type="RouteRequestType"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_REF_ID_PAIRS" type="RouteRefIDs"
                minOccurs="0" maxOccurs="3000">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BOOKNAME" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_MIFID_II_INSTRUCTION"
                type="MifidTradingInsructionEnum" minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GPI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AS_OF_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AS_OF_TIME_MICROSEC" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TOMS_PXNUM" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ModifyOrderRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_INVESTOR_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ModifyOrderRequestEx">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_INVESTOR_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BUYSIDE_LEI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLIENT_IDENTIFICATION"
                type="MifidClientIdentification" minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SI" type="MifidIsSi" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_MIFID_II_INSTRUCTION"
                type="MifidTradingInsructionEnum" minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GPI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ModifyRouteRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_ID" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_COMM_TYPE" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_COMM_RATE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_FEES" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE_DESTINATION" type="String"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ModifyRouteWithStratRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_ID" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_COMM_TYPE" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_COMM_RATE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_FEES" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE_DESTINATION" type="String"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ModifyRouteRequestEx">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_ID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="OrderTypeEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="TifEnum" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_COMM_TYPE" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_COMM_RATE" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_FEES" type="Float64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ODD_LOT" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE_DESTINATION" type="String"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_NOTES" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_REQ" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GET_WARNINGS" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_TYPE" type="ModifyRequestType"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="DeleteOrderRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="DeleteOrderResponse">
            <description></description>
            <element name="STATUS" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CancelOrderRequestEx">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CancelOrderResponse">
            <description></description>
            <element name="STATUS" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CancelRouteRequest">
            <description></description>
            <element name="ROUTES" type="TranInfo" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CancelRouteRequestEx">
            <description></description>
            <element name="ID_TYPE" type="IdType">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="AssignTraderRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ASSIGNEE_TRADER_UUID" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADE_DESK" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="SellSideAckRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="SellSideRejectRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CreateBasketRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BASKET_NAME" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ManualFillRequest">
            <description>seqManualFillRequest</description>
            <element name="ROUTE_TO_FILL" type="TranInfo">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="FILLS" type="ManualFillDetails" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ManualFillResponse">
            <description>seqManualFillResponse</description>
            <element name="MESSAGE" id="0" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILL_ID" id="1" type="Int32"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ManualFillDetails">
            <description>seqManualFillDetails</description>
            <element name="EMSX_FILL_PRICE" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILL_AMOUNT" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILL_DATE_TIME" type="DateTimeFormat">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_MARKET" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_INDIA_EXCHANGE" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXECUTE_BROKER" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER_LEI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_CAPACITY" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRANSACTION_REPORTING_MIC" type="String"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER_SI" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_APA_MIC" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_OTC_FLAG" type="MifidOtcFlag" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_WAIVER_FLAG" type="MifidWaiverFlag"
                minOccurs="0" maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADE_REPORTING_INDICATOR"
                type="MifidTradeReportingIndicatorEnum" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="LegacyDateTime">
            <description>seqLegacyDateTime</description>
            <element name="EMSX_FILL_DATE" id="0" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILL_TIME" id="1" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILL_TIME_FORMAT" id="2"
                type="TimeFormatEnum">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILL_TIME_MICROSEC" id="3" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="CancelRouteResponse">
            <description></description>
            <element name="STATUS" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="OrderInfoRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_IS_AGGREGATED" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="OrderInfoResponse">
            <description></description>
            <element name="EMSX_TICKER" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SIDE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_POSITION" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_PORT_MGR" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_IDLE_AMOUNT" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_WORKING" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILLED" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TS_ORDNUM" type="Int64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AVG_PRICE" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FLAG" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SUB_FLAG" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_YELLOW_KEY" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BASKET_NAME" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_CREATE_DATE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_CREATE_TIME" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_UUID" type="Int64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STEP_OUT_BROKER" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="RouteInfoRequest">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_ID" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="RouteInfoResponse">
            <description></description>
            <element name="EMSX_LIMIT_PRICE" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_YIELD" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AVG_PRICE" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_CREATE_DATE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_CREATE_TIME" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_LAST_UPDATE_DATE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_LAST_UPDATE_TIME" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_DATE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILLED" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_IS_MANUAL_ROUTE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STATUS_ID" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STATUS" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_ID" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LOC_BROKER" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BLOT_SEQ_NUM" type="Int64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BLOT_DATE" type="Int64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_COMM_TYPE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_COMM_RATE" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_COMM_AMOUNT" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LSTTR2ID0" type="Int64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LSTTR2ID1" type="Int64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PARAMS" type="Strategy"
                minOccurs="0" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_FIELD_NAMES" type="String"
                minOccurs="0" maxOccurs="20">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetTeamsRequest">
            <description></description>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetTeamsResponse">
            <description></description>
            <element name="TEAMS" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetAllFieldMetaDataRequest">
            <description></description>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetAllFieldMetaDataResponse">
            <description></description>
            <element name="MetaData" type="FieldMetaData" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetFieldMetaDataRequest">
            <description></description>
            <element name="EMSX_FIELD_NAMES" type="String" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetFieldMetaDataResponse">
            <description></description>
            <element name="MetaData" type="FieldMetaData" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetAssetClassRequest">
            <description></description>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetAssetClassResponse">
            <description></description>
            <element name="EMSX_ASSET_CLASS" type="AssetClassEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokersWithAssetClassRequest">
            <description></description>
            <element name="EMSX_ASSET_CLASS" type="AssetClassEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokersWithAssetClassResponse">
            <description></description>
            <element name="EMSX_BROKERS" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokerStrategiesWithAssetClassRequest">
            <description></description>
            <element name="EMSX_ASSET_CLASS" type="AssetClassEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokerStrategiesWithAssetClassResponse">
            <description></description>
            <element name="EMSX_STRATEGIES" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokerStrategyInfoWithAssetClassRequest">
            <description></description>
            <element name="EMSX_ASSET_CLASS" type="AssetClassEnum"
                minOccurs="1" maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokerStrategyInfoWithAssetClassResponse">
            <description></description>
            <element name="EMSX_STRATEGY_INFO" type="StrategyInfoDetails"
                minOccurs="0" maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokersRequest">
            <description></description>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokersResponse">
            <description></description>
            <element name="EMSX_BROKERS" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokerStrategiesRequest">
            <description></description>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokerStrategiesResponse">
            <description></description>
            <element name="EMSX_STRATEGIES" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokerStrategyInfoRequest">
            <description></description>
            <element name="EMSX_TICKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY" type="String" minOccurs="1"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="REQUEST_EXT" type="String" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REQUEST_SEQ" type="Int64" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetBrokerStrategyInfoResponse">
            <description></description>
            <element name="EMSX_STRATEGY_INFO" type="StrategyInfoDetails"
                minOccurs="0" maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="OrderStaticData">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="OrderStaticDataList">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32" minOccurs="0"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="RouteStaticData">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_ID" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="TranInfo">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_ID" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ErrorInfoResponse">
            <description></description>
            <element name="ERROR_CODE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ERROR_MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="TranErrorInfoResponse">
            <description></description>
            <element name="EMSX_SEQUENCE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ERROR_CODE" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ERROR_MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GroupRouteResponse">
            <description></description>
            <element name="EMSX_SUCCESS_ROUTES" type="TranInfo" minOccurs="0"
                maxOccurs="3000">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FAILED_ROUTES" type="TranErrorInfoResponse"
                minOccurs="0" maxOccurs="3000">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_ID" type="String" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="AssignTraderResponse">
            <description></description>
            <element name="EMSX_ASSIGN_TRADER_SUCCESSFUL_ORDERS"
                type="TranInfo" minOccurs="0" maxOccurs="3000">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ASSIGN_TRADER_FAILED_ORDERS"
                type="TranErrorInfoResponse" minOccurs="0" maxOccurs="3000">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ALL_SUCCESS" type="Boolean">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="StatusResponse">
            <description></description>
            <element name="STATUS" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MESSAGE" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="OrderRouteFields">
            <description></description>
            <element name="MSG_SUB_TYPE" id="1" type="String" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EVENT_STATUS" id="2" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>Special field</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="API_SEQ_NUM" id="3" type="Int64" minOccurs="1"
                maxOccurs="1">
                <description>Special field</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SEQUENCE" id="4" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>Static:O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_ID" id="5" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description>Static:O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILL_ID" id="6" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description>Static:O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SIDE" id="7" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AMOUNT" id="8" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_FILLED" id="9" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_AVG_PRICE" id="10" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER" id="11" type="String" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_WORKING" id="12" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TICKER" id="13" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE" id="14" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_CREATE_TIME" id="15" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Static:Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIF" id="16" type="String" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_LAST_UPDATE_TIME" id="17" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIME_STAMP" id="18" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_TYPE" id="19" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STATUS" id="20" type="String" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_IDLE_AMOUNT" id="21" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_STYLE" id="22" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_PRICE" id="23" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LIMIT_PRICE" id="24" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REMAIN_BALANCE" id="25" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER" id="26" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_DAY_FILL" id="27" type="Int32" minOccurs="0"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_DAY_AVG_PRICE" id="28" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_DATE" id="29" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NOTES" id="30" type="String" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ACCOUNT" id="31" type="String" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TYPE" id="32" type="String" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_PRINCIPAL" id="33" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_AMOUNT" id="34" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SEC_NAME" id="35" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_PORT_MGR" id="36" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GTD_DATE" id="37" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_PORT_NAME" id="38" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_END_TIME" id="39" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_PERCENT_FILLED" id="40" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_STRATEGY" id="41" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_LEG_QUANTITY" id="42" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_TOTAL_QUANTITY" id="43" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_REMAIN_BALANCE" id="44" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_START_TIME" id="45" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BASKET_NAME" id="46" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_PERCENT_REMAIN" id="47" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_CREATE_DATE" id="48" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Static:Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_P_A" id="49" type="String" minOccurs="0"
                maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_ACCOUNT" id="50" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLEARING_FIRM" id="51" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STOP_PRICE" id="52" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SETTLE_DATE" id="53" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ISIN" id="54" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER_COMM" id="55" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_WORK_PRICE" id="56" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SEDOL" id="57" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_HAND_INSTRUCTION" id="58" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TS_ORDNUM" id="59" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_COMM_RATE" id="60" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXEC_INSTRUCTION" id="61" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORD_REF_ID" id="62" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PART_RATE2" id="63" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_COMM_RATE" id="64" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_COMM_AMOUNT" id="65" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_TYPE" id="66" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REASON_CODE" id="67" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_REASON_DESC" id="68" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STRATEGY_PART_RATE1" id="69" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BSE_FILLED" id="70" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_QUEUED_TIME" id="71" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NSE_FILLED" id="72" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BASKET_NUM" id="73" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_FILL_TIME" id="74" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_NSE_AVG_PRICE" id="75" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CFD_FLAG" id="76" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BSE_AVG_PRICE" id="77" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>Static:O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_NET_MONEY" id="78" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ASSIGNED_TRADER" id="79" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORIGINATE_TRADER" id="80" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_USER_FEES" id="81" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_FILL_DATE" id="82" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_INVESTOR_ID" id="83" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_POSITION" id="84" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_PORT_NUM" id="85" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ASSET_CLASS" id="86" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORIGINATE_TRADER_FIRM" id="87" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_YELLOW_KEY" id="88" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_QUEUED_DATE" id="89" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADE_DESK" id="90" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXECUTE_BROKER" id="91" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_COMM_DIFF_FLAG" id="92" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_EXCHANGE_DESTINATION" id="93" type="String"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CURRENCY_PAIR" id="94" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Static:O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_MISC_FEES" id="95" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_STEP_OUT_BROKER" id="96" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_URGENCY_LEVEL" id="97" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_RATIO" id="98" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_DIR_BROKER_FLAG" id="99" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_START_AMOUNT" id="100" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ARRIVAL_PRICE" id="101" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_PRODUCT" id="102" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_IS_MANUAL_ROUTE" id="103" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>Static:Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_UNDERLYING_TICKER" id="104" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_NUM_LEGS" id="105" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADER_NOTES" id="106" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_ACCOUNT" id="107" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_SHARES" id="108" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_PRICE" id="109" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_MARKET" id="110" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRAD_UUID" id="111" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_PM_UUID" id="112" type="Int32" minOccurs="1"
                maxOccurs="1">
                <description>Static:Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ML_ID" id="113" type="String" minOccurs="1"
                maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BLOCK_ID" id="114" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_REF_ID" id="115" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MSG_TYPE" id="116" type="String" minOccurs="1"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER_STATUS" id="117" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BUYSIDE_LEI" id="118" type="String"
                minOccurs="0" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER_LEI" id="119" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRADE_REPORTING_INDICATOR" id="120"
                type="String" minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TRANSACTION_REPORTING_MIC" id="121"
                type="String" minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_APA_MIC" id="122" type="String" minOccurs="0"
                maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_OTC_FLAG" id="123" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_WAIVER_FLAG" id="124" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_CAPACITY" id="125" type="String"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CLIENT_IDENTIFICATION" id="126" type="String"
                minOccurs="0" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_SI" id="127" type="String" minOccurs="0"
                maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_MIFID_II_INSTRUCTION" id="128" type="String"
                minOccurs="0" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER_SI" id="129" type="String"
                minOccurs="0" maxOccurs="1">
                <description>R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_CREATE_TIME_MICROSEC" id="130"
                type="Float64" minOccurs="0" maxOccurs="1">
                <description>Static:Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_LAST_UPDATE_TIME_MICROSEC" id="131"
                type="Float64" minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_TIME_STAMP_MICROSEC" id="132" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_QUEUED_TIME_MICROSEC" id="133" type="Float64"
                minOccurs="1" maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LAST_FILL_TIME_MICROSEC" id="134"
                type="Float64" minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_GPI" id="135" type="String" minOccurs="0"
                maxOccurs="1">
                <description>O,R</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_AS_OF_DATE" id="136" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ORDER_AS_OF_TIME_MICROSEC" id="137"
                type="Float64" minOccurs="1" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_AS_OF_DATE" id="138" type="Int32"
                minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_ROUTE_AS_OF_TIME_MICROSEC" id="139"
                type="Float64" minOccurs="1" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEG_FILL_SIDE" id="140" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEG_FILL_DATE_ADDED" id="141" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEG_FILL_TIME_ADDED" id="142" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEG_FILL_SHARES" id="143" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEG_FILL_PRICE" id="144" type="Float64"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEG_FILL_SEQ_NO" id="145" type="Int32"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_LEG_FILL_TICKER" id="146" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE1" id="147" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE2" id="148" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE3" id="149" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE4" id="150" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_CUSTOM_NOTE5" id="151" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_MOD_PEND_STATUS" id="152" type="String"
                minOccurs="0" maxOccurs="1">
                <description>Order</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="EMSX_BROKER_CLIENT_ORDER_ID" id="153"
                type="String" minOccurs="0" maxOccurs="1">
                <description>Route</description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <choiceType name="RouteRequestType">
            <description></description>
            <element name="Multileg" type="MultilegFields">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Spread" type="SpreadFields">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="ModifyRequestType">
            <description></description>
            <element name="Multileg" type="MultilegID">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="IdType">
            <description></description>
            <element name="OrderRoute" type="TranInfo" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Multileg" type="MultilegID" minOccurs="1"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="IdentityType">
            <description></description>
            <element name="EMSX_TRADER_UUID" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="DateTimeFormat">
            <description>choiceDateTimeFormat</description>
            <element name="Legacy" id="0" type="LegacyDateTime">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="Request">
            <description></description>
            <element name="OrderInfo" type="OrderInfoRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteInfo" type="RouteInfoRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrder" type="CreateOrderRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrderAndRoute"
                type="CreateOrderAndRouteRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrderAndRouteManually"
                type="CreateOrderAndRouteRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyOrder" type="ModifyOrderRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="DeleteOrder" type="DeleteOrderRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Route" type="RouteOrderRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteManually" type="RouteOrderRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyRoute" type="ModifyRouteRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CancelRoute" type="CancelRouteRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetTeams" type="GetTeamsRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetFieldMetaData" type="GetFieldMetaDataRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetAllFieldMetaData"
                type="GetAllFieldMetaDataRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokers" type="GetBrokersRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokerStrategies"
                type="GetBrokerStrategiesRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokerStrategyInfo"
                type="GetBrokerStrategyInfoRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrderAndRouteWithStrat"
                type="CreateOrderWithStratRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteWithStrat" type="RouteOrderWithStratRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyRouteWithStrat"
                type="ModifyRouteWithStratRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GroupRouteWithStrat"
                type="GroupRouteWithStratRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrderAndRouteEx"
                type="CreateOrderAndRouteRequestEx">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteEx" type="RouteOrderRequestEx">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyRouteEx" type="ModifyRouteRequestEx">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GroupRouteEx" type="GroupRouteRequestEx">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteManuallyEx" type="RouteOrderRequestEx">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetAssetClass" type="GetAssetClassRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokerStrategiesWithAssetClass"
                type="GetBrokerStrategiesWithAssetClassRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokerStrategyInfoWithAssetClass"
                type="GetBrokerStrategyInfoWithAssetClassRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokersWithAssetClass"
                type="GetBrokersWithAssetClassRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CancelRouteEx" type="CancelRouteRequestEx">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="AssignTrader" type="AssignTraderRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="SellSideAck" type="SellSideAckRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="SellSideReject" type="SellSideRejectRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CancelOrderEx" type="CancelOrderRequestEx">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyOrderEx" type="ModifyOrderRequestEx">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ManualFill" type="ManualFillRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetTraders" type="GetTradersRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetTradeDesks" type="GetTradeDesksRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateBasket" type="CreateBasketRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="Response">
            <description></description>
            <element name="ErrorInfo" type="ErrorInfoResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OrderInfo" type="OrderInfoResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteInfo" type="RouteInfoResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrder" type="OrderStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrderAndRoute" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrderAndRouteManually"
                type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyOrder" type="OrderStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="DeleteOrder" type="DeleteOrderResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Route" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteManually" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyRoute" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CancelRoute" type="CancelRouteResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetTeams" type="GetTeamsResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetFieldMetaData" type="GetFieldMetaDataResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetAllFieldMetaData"
                type="GetAllFieldMetaDataResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokers" type="GetBrokersResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokerStrategies"
                type="GetBrokerStrategiesResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokerStrategyInfo"
                type="GetBrokerStrategyInfoResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrderAndRouteWithStrat"
                type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteWithStrat" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyRouteWithStrat" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GroupRouteWithStrat" type="GroupRouteResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateOrderAndRouteEx" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteEx" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyRouteEx" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GroupRouteEx" type="GroupRouteResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteManuallyEx" type="RouteStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetAssetClass" type="GetAssetClassResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokerStrategiesWithAssetClass"
                type="GetBrokerStrategiesWithAssetClassResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokerStrategyInfoWithAssetClass"
                type="GetBrokerStrategyInfoWithAssetClassResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetBrokersWithAssetClass"
                type="GetBrokersWithAssetClassResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CancelRouteEx" type="CancelRouteResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="AssignTrader" type="AssignTraderResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="SellSideAck" type="StatusResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="SellSideReject" type="StatusResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CancelOrderEx" type="CancelOrderResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ModifyOrderEx" type="OrderStaticData">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ManualFill" type="ManualFillResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetTraders" type="GetTradersResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="GetTradeDesks" type="GetTradeDesksResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CreateBasket" type="OrderStaticDataList">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <enumerationType name="FieldTypeEnum" type="String">
            <description></description>
            <enumerator name="Bool">
                <description></description>
                <value>
                    <String>Bool</String>
                </value>
            </enumerator>
            <enumerator name="Double">
                <description></description>
                <value>
                    <String>Double</String>
                </value>
            </enumerator>
            <enumerator name="Int32">
                <description></description>
                <value>
                    <String>Int32</String>
                </value>
            </enumerator>
            <enumerator name="Int64">
                <description></description>
                <value>
                    <String>Int64</String>
                </value>
            </enumerator>
            <enumerator name="String">
                <description></description>
                <value>
                    <String>String</String>
                </value>
            </enumerator>
            <enumerator name="Date">
                <description></description>
                <value>
                    <String>Date</String>
                </value>
            </enumerator>
            <enumerator name="Time">
                <description></description>
                <value>
                    <String>Time</String>
                </value>
            </enumerator>
            <enumerator name="Unknown">
                <description></description>
                <value>
                    <String>Unknown</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="SideEnum" type="String">
            <description></description>
            <enumerator name="BUY">
                <description></description>
                <value>
                    <String>BUY</String>
                </value>
            </enumerator>
            <enumerator name="BUYM">
                <description></description>
                <value>
                    <String>BUYM</String>
                </value>
            </enumerator>
            <enumerator name="COVR">
                <description></description>
                <value>
                    <String>COVR</String>
                </value>
            </enumerator>
            <enumerator name="SELL">
                <description></description>
                <value>
                    <String>SELL</String>
                </value>
            </enumerator>
            <enumerator name="SHRT">
                <description></description>
                <value>
                    <String>SHRT</String>
                </value>
            </enumerator>
            <enumerator name="SHRX">
                <description></description>
                <value>
                    <String>SHRX</String>
                </value>
            </enumerator>
            <enumerator name="SLPL">
                <description></description>
                <value>
                    <String>SLPL</String>
                </value>
            </enumerator>
            <enumerator name="B/O">
                <description></description>
                <value>
                    <String>B/O</String>
                </value>
            </enumerator>
            <enumerator name="B/C">
                <description></description>
                <value>
                    <String>B/C</String>
                </value>
            </enumerator>
            <enumerator name="S/C">
                <description></description>
                <value>
                    <String>S/C</String>
                </value>
            </enumerator>
            <enumerator name="S/O">
                <description></description>
                <value>
                    <String>S/O</String>
                </value>
            </enumerator>
            <enumerator name="UNDI">
                <description></description>
                <value>
                    <String>UNDI</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="SettleTypeEnum" type="String">
            <description></description>
            <enumerator name="Regular">
                <description></description>
                <value>
                    <String>Regular</String>
                </value>
            </enumerator>
            <enumerator name="Cash">
                <description></description>
                <value>
                    <String>Cash</String>
                </value>
            </enumerator>
            <enumerator name="Next Day">
                <description></description>
                <value>
                    <String>Next Day</String>
                </value>
            </enumerator>
            <enumerator name="T+2">
                <description></description>
                <value>
                    <String>T+2</String>
                </value>
            </enumerator>
            <enumerator name="T+3">
                <description></description>
                <value>
                    <String>T+3</String>
                </value>
            </enumerator>
            <enumerator name="T+4">
                <description></description>
                <value>
                    <String>T+4</String>
                </value>
            </enumerator>
            <enumerator name="Future">
                <description></description>
                <value>
                    <String>Future</String>
                </value>
            </enumerator>
            <enumerator name="When Issued">
                <description></description>
                <value>
                    <String>When Issued</String>
                </value>
            </enumerator>
            <enumerator name="T+5">
                <description></description>
                <value>
                    <String>T+5</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="OrderTypeEnum" type="String">
            <description></description>
            <enumerator name="CD">
                <description></description>
                <value>
                    <String>CD</String>
                </value>
            </enumerator>
            <enumerator name="FUN">
                <description></description>
                <value>
                    <String>FUN</String>
                </value>
            </enumerator>
            <enumerator name="LMT">
                <description></description>
                <value>
                    <String>LMT</String>
                </value>
            </enumerator>
            <enumerator name="LOC">
                <description></description>
                <value>
                    <String>LOC</String>
                </value>
            </enumerator>
            <enumerator name="MKT">
                <description></description>
                <value>
                    <String>MKT</String>
                </value>
            </enumerator>
            <enumerator name="MOC">
                <description></description>
                <value>
                    <String>MOC</String>
                </value>
            </enumerator>
            <enumerator name="OC">
                <description></description>
                <value>
                    <String>OC</String>
                </value>
            </enumerator>
            <enumerator name="SL">
                <description></description>
                <value>
                    <String>SL</String>
                </value>
            </enumerator>
            <enumerator name="ST">
                <description></description>
                <value>
                    <String>ST</String>
                </value>
            </enumerator>
            <enumerator name="PEG">
                <description></description>
                <value>
                    <String>PEG</String>
                </value>
            </enumerator>
            <enumerator name="MKTL">
                <description></description>
                <value>
                    <String>MKTL</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="TifEnum" type="String">
            <description></description>
            <enumerator name="DAY">
                <description></description>
                <value>
                    <String>DAY</String>
                </value>
            </enumerator>
            <enumerator name="FOK">
                <description></description>
                <value>
                    <String>FOK</String>
                </value>
            </enumerator>
            <enumerator name="GTC">
                <description></description>
                <value>
                    <String>GTC</String>
                </value>
            </enumerator>
            <enumerator name="GTD">
                <description></description>
                <value>
                    <String>GTD</String>
                </value>
            </enumerator>
            <enumerator name="GTX">
                <description></description>
                <value>
                    <String>GTX</String>
                </value>
            </enumerator>
            <enumerator name="IOC">
                <description></description>
                <value>
                    <String>IOC</String>
                </value>
            </enumerator>
            <enumerator name="OPG">
                <description></description>
                <value>
                    <String>OPG</String>
                </value>
            </enumerator>
            <enumerator name="CLO">
                <description></description>
                <value>
                    <String>CLO</String>
                </value>
            </enumerator>
            <enumerator name="AUC">
                <description></description>
                <value>
                    <String>AUC</String>
                </value>
            </enumerator>
            <enumerator name="DAY+">
                <description></description>
                <value>
                    <String>DAY+</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="AssetClassEnum" type="String">
            <description></description>
            <enumerator name="EQTY">
                <description></description>
                <value>
                    <String>EQTY</String>
                </value>
            </enumerator>
            <enumerator name="OPT">
                <description></description>
                <value>
                    <String>OPT</String>
                </value>
            </enumerator>
            <enumerator name="FUT">
                <description></description>
                <value>
                    <String>FUT</String>
                </value>
            </enumerator>
            <enumerator name="MULTILEG_OPT">
                <description></description>
                <value>
                    <String>MULTILEG_OPT</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="MifidTradeReportingIndicatorEnum"
            type="String">
            <description></description>
            <enumerator name="NOT_REPORTED">
                <description></description>
                <value>
                    <String>N</String>
                </value>
            </enumerator>
            <enumerator name="VENUE_ONBOOK">
                <description></description>
                <value>
                    <String>O</String>
                </value>
            </enumerator>
            <enumerator name="SI_SELLER">
                <description></description>
                <value>
                    <String>S</String>
                </value>
            </enumerator>
            <enumerator name="SI_BUYER">
                <description></description>
                <value>
                    <String>B</String>
                </value>
            </enumerator>
            <enumerator name="NONSI_SELLER">
                <description></description>
                <value>
                    <String>X</String>
                </value>
            </enumerator>
            <enumerator name="DELEGATED_REPORTING">
                <description></description>
                <value>
                    <String>D</String>
                </value>
            </enumerator>
            <enumerator name="WILL_BE_REPORTED">
                <description></description>
                <value>
                    <String>W</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="MifidTradingInsructionEnum" type="String">
            <description></description>
            <enumerator name="NO_RESTRICTION">
                <description></description>
                <value>
                    <String>No restriction</String>
                </value>
            </enumerator>
            <enumerator name="VENUE">
                <description></description>
                <value>
                    <String>Venue</String>
                </value>
            </enumerator>
            <enumerator name="SI">
                <description></description>
                <value>
                    <String>SI</String>
                </value>
            </enumerator>
            <enumerator name="SI_OR_VENUE">
                <description></description>
                <value>
                    <String>SI or venue</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="MifidClientIdentification" type="String">
            <description></description>
            <enumerator name="AGGR">
                <description></description>
                <value>
                    <String>AGGR</String>
                </value>
            </enumerator>
            <enumerator name="PNAL">
                <description></description>
                <value>
                    <String>PNAL</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="MifidIsSi" type="String">
            <description></description>
            <enumerator name="Y">
                <description></description>
                <value>
                    <String>Y</String>
                </value>
            </enumerator>
            <enumerator name="N">
                <description></description>
                <value>
                    <String>N</String>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="MifidOtcFlag" type="Int32">
            <description></description>
            <enumerator name="BENC">
                <description></description>
                <value>
                    <Int32>64</Int32>
                </value>
            </enumerator>
            <enumerator name="SDIV">
                <description></description>
                <value>
                    <Int32>13</Int32>
                </value>
            </enumerator>
            <enumerator name="TNCP">
                <description></description>
                <value>
                    <Int32>16</Int32>
                </value>
            </enumerator>
            <enumerator name="ACTX">
                <description></description>
                <value>
                    <Int32>37</Int32>
                </value>
            </enumerator>
            <enumerator name="RPRI">
                <description></description>
                <value>
                    <Int32>14</Int32>
                </value>
            </enumerator>
            <enumerator name="ILQD">
                <description></description>
                <value>
                    <Int32>7</Int32>
                </value>
            </enumerator>
            <enumerator name="SIZE">
                <description></description>
                <value>
                    <Int32>8</Int32>
                </value>
            </enumerator>
            <enumerator name="TPAC">
                <description></description>
                <value>
                    <Int32>65</Int32>
                </value>
            </enumerator>
            <enumerator name="XFPH">
                <description></description>
                <value>
                    <Int32>2</Int32>
                </value>
            </enumerator>
            <enumerator name="LRGS">
                <description></description>
                <value>
                    <Int32>6</Int32>
                </value>
            </enumerator>
            <enumerator name="NPFT">
                <description></description>
                <value>
                    <Int32>15</Int32>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="MifidWaiverFlag" type="Int32">
            <description></description>
            <enumerator name="RFPT">
                <description></description>
                <value>
                    <Int32>3</Int32>
                </value>
            </enumerator>
            <enumerator name="NLIQ">
                <description></description>
                <value>
                    <Int32>0</Int32>
                </value>
            </enumerator>
            <enumerator name="OILQ">
                <description></description>
                <value>
                    <Int32>1</Int32>
                </value>
            </enumerator>
            <enumerator name="PRIC">
                <description></description>
                <value>
                    <Int32>2</Int32>
                </value>
            </enumerator>
            <enumerator name="LRGS">
                <description></description>
                <value>
                    <Int32>9</Int32>
                </value>
            </enumerator>
            <enumerator name="OM">
                <description></description>
                <value>
                    <Int32>10</Int32>
                </value>
            </enumerator>
            <enumerator name="ILQD">
                <description></description>
                <value>
                    <Int32>4</Int32>
                </value>
            </enumerator>
            <enumerator name="SIZE">
                <description></description>
                <value>
                    <Int32>5</Int32>
                </value>
            </enumerator>
        </enumerationType>
        <enumerationType name="TimeFormatEnum" type="String">
            <description></description>
            <enumerator name="Hhmmss">
                <description></description>
                <value>
                    <String>Hhmmss</String>
                </value>
            </enumerator>
            <enumerator name="SecondsFromMidnight">
                <description></description>
                <value>
                    <String>SecondsFromMidnight</String>
                </value>
            </enumerator>
        </enumerationType>
    </schema>
</ServiceDefinition>
"""

EMSX_HISTORY_SERVICE = """<?xml version="1.0" encoding="UTF-8" ?>
<ServiceDefinition xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    name="blp.emsx.history.uat" version="1.4.0.2">
    <service name="//blp/emsx.history.uat" version="1.4.0.2">
        <operation name="GetFills" serviceId="1073943349">
            <request>request</request>
            <requestSelection>GetFills</requestSelection>
            <response>response</response>
            <responseSelection>GetFillsResponse</responseSelection>
            <responseSelection>ErrorResponse</responseSelection>
            <timeout>120</timeout>
        </operation>
        <publisherSupportsRecap>false</publisherSupportsRecap>
        <authoritativeSourceSupportsRecap>true</authoritativeSourceSupportsRecap>
        <isInfrastructureService>false</isInfrastructureService>
        <isMetered>false</isMetered>
        <appendMtrId>false</appendMtrId>
        <persistentLastValueCache>false</persistentLastValueCache>
    </service>
    <schema>
        <sequenceType name="GetFillsRequest">
            <description>seqGetFillsRequest</description>
            <element name="FromDateTime" id="0" type="Datetime">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ToDateTime" id="1" type="Datetime">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Scope" id="2" type="Scope">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="FilterBy" id="3" type="FilterBy" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="OrderRouteId">
            <description>seqOrderRouteId</description>
            <element name="OrderId" id="0" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteId" id="1" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="GetFillsResponse">
            <description>seqGetFillsResponse</description>
            <element name="Fills" type="FillItem" maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="FillItem">
            <description>seqFillItem</description>
            <element name="Ticker" id="0" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Exchange" id="1" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Side" id="2" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="TIF" id="3" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Type" id="4" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OrderId" id="5" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteId" id="6" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="FillId" id="7" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="CorrectedFillId" id="8" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MultilegId" id="9" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="IsLeg" id="10" type="Boolean">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="FillPrice" id="11" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="FillShares" id="12" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="TraderUuid" id="13" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ExecutingBroker" id="14" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ReroutedBroker" id="15" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="BasketName" id="16" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="DateTimeOfFill" id="17" type="Datetime">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Account" id="18" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="LastCapacity" id="19" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Liquidity" id="20" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="LastMarket" id="21" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="BasketId" id="22" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="BlockId" id="23" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="IsCfd" id="24" type="Boolean">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ClearingAccount" id="25" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ClearingFirm" id="26" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Currency" id="27" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Cusip" id="28" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Isin" id="29" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="LocalExchangeSymbol" id="30" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="LocateRequired" id="31" type="Boolean">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="LocateBroker" id="32" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="LocateId" id="33" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OrderReferenceId" id="34" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteNotes" id="35" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="SecurityName" id="36" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Sedol" id="37" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Broker" id="38" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteCommissionAmount" id="39" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteCommissionRate" id="40" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="LimitPrice" id="41" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteNetMoney" id="42" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteShares" id="43" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="SettlementDate" id="44" type="Date" minOccurs="0"
                maxOccurs="1">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="UserCommissionAmount" id="45" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="UserCommissionRate" id="46" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="UserFees" id="47" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="UserNetMoney" id="48" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OriginatingTraderUuid" id="49" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteExecutionInstruction" id="50" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="RouteHandlingInstruction" id="51" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OrderExecutionInstruction" id="52" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OrderHandlingInstruction" id="53" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OrderInstruction" id="54" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="YellowKey" id="55" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="InvestorID" id="56" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Amount" id="57" type="Float64">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="StopPrice" id="58" type="Float32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="StrategyType" id="59" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ContractExpDate" id="60" type="Date">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="AssetClass" id="61" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="BBGID" id="62" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="TraderName" id="63" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OrderOrigin" id="64" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="OCCSymbol" id="65" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ExecType" id="66" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ExecPrevSeqNo" id="67" type="Int32">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidBuysideLei" id="68" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidAggrFlag" id="69" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidIsSi" id="70" type="Boolean">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidTradeInstr" id="71" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidGpi" id="72" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidSellsideLei" id="73" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidSellsideTri" id="74" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidSellsideTrMic" id="75" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidSellsideSiMic" id="76" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidSellsideApaMic" id="77" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidSellsideOtcFlag" id="78" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="MifidSellsideWaiverFlag" id="79" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="BrokerExecId" id="80" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="BrokerOrderId" id="81" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="NyOrderCreateAsOfDateTime" id="82" type="Datetime">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Mpid" id="83" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="NyTranCreateAsOfDateTime" id="84" type="Datetime">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <sequenceType name="ErrorResponse">
            <description>seqErrorResponse</description>
            <element name="ErrorCode" type="ErrorCode">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ErrorMsg" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </sequenceType>
        <choiceType name="request">
            <description>choicerequest</description>
            <element name="GetFills" id="0" type="GetFillsRequest">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="Scope">
            <description>choiceScope</description>
            <element name="Uuids" id="0" type="Int32" maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="TradingSystem" id="1" type="Boolean">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Team" id="2" type="String">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="FilterBy">
            <description>choiceFilterBy</description>
            <element name="OrdersAndRoutes" id="0" type="OrderRouteId"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Basket" id="1" type="String" maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="Multileg" id="2" type="String"
                maxOccurs="unbounded">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <choiceType name="response">
            <description>choiceresponse</description>
            <element name="GetFillsResponse" id="0" type="GetFillsResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
            <element name="ErrorResponse" id="1" type="ErrorResponse">
                <description></description>
                <cacheable>true</cacheable>
                <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>
            </element>
        </choiceType>
        <enumerationType name="ErrorCode" type="String">
            <description></description>
            <enumerator name="ERROR_INVALID_INPUT">
                <description></description>
                <value>
                    <String>ERROR_INVALID_INPUT</String>
                </value>
            </enumerator>
            <enumerator name="ERROR_INTERNAL">
                <description></description>
                <value>
                    <String>ERROR_INTERNAL</String>
                </value>
            </enumerator>
            <enumerator name="ERROR_PERMISSION">
                <description></description>
                <value>
                    <String>ERROR_PERMISSION</String>
                </value>
            </enumerator>
            <enumerator name="ERROR_INVALID_AUTHENTICATION_MODE">
                <description></description>
                <value>
                    <String>ERROR_INVALID_AUTHENTICATION_MODE</String>
                </value>
            </enumerator>
        </enumerationType>
    </schema>
</ServiceDefinition>
"""
