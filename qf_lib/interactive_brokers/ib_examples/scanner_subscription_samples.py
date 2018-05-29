"""
Copyright (C) 2016 Interactive Brokers LLC. All rights reserved.  This code is
subject to the terms and conditions of the IB API Non-Commercial License or the
 IB API Commercial License, as applicable. 
"""

from ibapi.object_implem import Object
from ibapi.scanner import ScannerSubscription


class ScannerSubscriptionSamples(Object):

    @staticmethod
    def HotUSStkByVolume():
        # Hot US stocks by volume
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "HOT_BY_VOLUME"
        return scanSub

    @staticmethod
    def TopPercentGainersIbis():
        # Top % gainers at IBIS
        scanSub = ScannerSubscription()
        scanSub.instrument = "STOCK.EU"
        scanSub.locationCode = "STK.EU.IBIS"
        scanSub.scanCode = "TOP_PERC_GAIN"
        return scanSub

    @staticmethod
    def MostActiveFutSoffex():
        # Most active futures at SOFFEX
        scanSub = ScannerSubscription()
        scanSub.instrument = "FUT.EU"
        scanSub.locationCode = "FUT.EU.SOFFEX"
        scanSub.scanCode = "MOST_ACTIVE"
        return scanSub

    @staticmethod
    def HighOptVolumePCRatioUSIndexes():
        # High option volume P/C ratio US indexes
        scanSub = ScannerSubscription()
        scanSub.instrument = "IND.US"
        scanSub.locationCode = "IND.US"
        scanSub.scanCode = "HIGH_OPT_VOLUME_PUT_CALL_RATIO"
        return scanSub
