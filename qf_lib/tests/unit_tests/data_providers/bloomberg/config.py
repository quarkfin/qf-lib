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

REF_DATA_SERVICE_URI = """<?xml version="1.0" encoding="UTF-8" ?>\
<ServiceDefinition name="blp.refdata" version="1.0.1.0">\
   <service name="//blp/refdata" version="1.0.0.0">\
      <operation name="HistoricalDataRequest">\
        <request>HistoricalDataRequest</request>\
        <response>Response</response>\
        <responseSelection>HistoricalDataResponse</responseSelection>\
      </operation>\
        <operation name="IntradayBarRequest">\
        <request>IntradayBarRequest</request>\
        <response>Response</response>\
        <responseSelection>IntradayBarResponse</responseSelection>\
      </operation>\
   </service>\
   <schema>\
    <sequenceType name="HistoricalDataRequest">\
        <element name="securities" type="String" maxOccurs="unbounded"/>\
        <element name="fields" type="String" maxOccurs="unbounded"/>\
        <element name="overrides" type="FieldOverride" minOccurs="0" maxOccurs="unbounded"/>\
    </sequenceType>\
    <sequenceType name="IntradayBarRequest">\
        <element name="security" type="String" maxOccurs="unbounded"/>\
        <element name="startDateTime" type="Datetime" maxOccurs="unbounded"/>\
        <element name="endDateTime" type="Datetime" maxOccurs="unbounded"/>\
        <element name="interval" type="String" maxOccurs="unbounded"/>\
    </sequenceType>\
    <sequenceType name="FieldOverride">\
        <element name="fieldId" type="String"/>\
        <element name="value" type="String"/>\
    </sequenceType>\
    <choiceType name="Response">\
        <element name="HistoricalDataResponse" type="HistoricalDataResponseType">\
            <cacheable>true</cacheable>\
            <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>\
        </element>\
        <element name="IntradayBarResponse" type="IntradayBarResponseType">\
            <cacheable>true</cacheable>\
            <cachedOnlyOnInitialPaint>false</cachedOnlyOnInitialPaint>\
        </element>\
    </choiceType>\
    <sequenceType name="HistoricalDataResponseType">\
        <element name="responseError" type="ErrorInfo"       />\
        <element name="securityData"  type="HistoricalSecurityData" minOccurs="0" maxOccurs="1"/>\
    </sequenceType>\
        <sequenceType name="IntradayBarResponseType">\
        <element name="responseError" type="ErrorInfo"       />\
        <element name="barData"  type="BarData"\
                                         minOccurs="0" maxOccurs="1"/>\
    </sequenceType>\
    <sequenceType name="HistoricalSecurityData">\
        <element name="security"         type="String"/>\
        <element name="eidData"          type="Int64"\
                                           minOccurs="0" maxOccurs="unbounded" />\
        <element name="securityError"    type="ErrorInfo"   \
                                           minOccurs="0" maxOccurs="1"/>\
        <element name="fieldExceptions"  type="FieldException"\
                                          minOccurs="0" maxOccurs="unbounded"/>\
        <element name="sequenceNumber"  type="Int64" \
                                          minOccurs="0" maxOccurs="1"/>\
        <element name="fieldData"       type="FieldData" minOccurs="1" maxOccurs="unbounded"/>\
    </sequenceType>\
    <sequenceType name="BarData">\
        <element name="eidData"          type="Int64" minOccurs="0" maxOccurs="unbounded" />\
        <element name="securityError"    type="ErrorInfo"   \
                                           minOccurs="0" maxOccurs="1"/>\
        <element name="fieldExceptions"  type="FieldException"\
                                          minOccurs="0" maxOccurs="unbounded"/>\
        <element name="barTickData"       type="BarTickData" minOccurs="1" maxOccurs="unbounded"/>\
    </sequenceType>\
    <sequenceType name="FieldData">\
        <element name="date"       type="String"  />\
        <element name="PX_LAST"    type="Float64"  />\
        <element name="PX_VOLUME"    type="Float64"  />\
    </sequenceType>\
    <sequenceType name="BarTickData">\
        <element name="time"       type="String"  />\
        <element name="open"    type="Float64"  />\
        <element name="high"    type="Float64"  />\
        <element name="low"    type="Float64"  />\
        <element name="close"    type="Float64"  />\
        <element name="volume"    type="Float64"  />\
    </sequenceType>\
    <sequenceType name="FieldException">\
      <element name="fieldId"    type="String"/> \
      <element name="errorInfo"  type="ErrorInfo"/>\
    </sequenceType>\
    <sequenceType name="ErrorInfo">\
      <element name="source"   type="String" />\
      <element name="code"     type="Int64"   />\
      <element name="category" type="String"  />\
      <element name="message"  type="String"/>\
      <element name="subcategory" type="String"\
                                  minOccurs="0" maxOccurs="1"/>\
    </sequenceType>\
    </schema>\
</ServiceDefinition>
"""
