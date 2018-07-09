# classdef VolatilityRiskPremiumVIXminusSPX < handle
#     %VOLATILITYRISKPREMIUM Summary of this class goes here
#     %   Detailed explanation goes here
#
#     properties
#         bh;                        % BloombergHelper
#
#         spxReturnsTimeseries;      % Timeseries of returns of SPX Index. Returns are presented as numbers (not in %)
#         spxVolTimeseries;          % Timeseries of realised volatility of SPX Index expressed as numbers (not in %)
#         vixPricesTimeseries;       % Timeseries of implied Volatility (VIX Index) expressed in percentage (not in numbers)
#
#         indicatorValue  = NaN;     % Value of the indicator = indicatorWindowSize day average of (VIX - (volWindowSize day historial vol of SPX * 100))
#                                    % Before the value is calculated it is NaN (Not a Number)
#
#         frequency       = 'daily';
#         averageFunction = @mean;
#     end
#
#     methods
#
#         function VP = VolatilityRiskPremiumVIXminusSPX()
#             % constructor
#             VP.bh = BloombergHelper();
#         end
#
#
#         function [message, allocation] = GetSignalForDate(VP, date)
#             % !!! apply the signal to a day following date !!!
#
#             % best parameters  as at 2015.03.01
#              volWindowSize       =  3;
#              indicatorWindowSize =  2;
#              threshold           = -2;
#              maxVixLevel         =  inf;
#
#              [message, allocation] = VP.GetSignalForParameters(date, volWindowSize, indicatorWindowSize, threshold, maxVixLevel);
#
#              nrOfDaysOfVIX     =  20;
#              stopLossParameter = -0.22;
#              maxStopLoss       = -3;
#
#              stopLoss = VP.CalculateStopLoss(nrOfDaysOfVIX, stopLossParameter, maxStopLoss);
#
#              message = sprintf('%s \r\nStop-loss = % 5.2f%% calculated as: max[(%0.3f) * sqrt(%d-day MA(VIX) * %d-day std(VIX)), %0.2f%%]',message, stopLoss, stopLossParameter, nrOfDaysOfVIX, nrOfDaysOfVIX, maxStopLoss);
#         end
#
#         function [message, allocation] = GetSignalForParameters(VP, date, volWindowSize, indicatorWindowSize, threshold, maxVixLevel)
#             VP.DownloadData(date);
#             VP.CalculateVolatilityOfSPX(volWindowSize);
#             VP.CalculateIndicator(indicatorWindowSize);
#             [message, allocation] = VP.CalculateSignal(threshold, maxVixLevel);
#
#             % add date to the message
#             message = sprintf('%s - %s', datestr(date,'yyyy-mm-dd'), message);
#         end
#
#         function DownloadData(VP, date)
#             toDate    = date;
#             fromDate  = toDate - 40;
#
#             spxPricesTimeseries    = VP.bh.GetHistoryForCommonDates('SPX Index', fromDate, toDate, 'PX_LAST', VP.frequency, []);
#             VP.vixPricesTimeseries = VP.bh.GetHistoryForCommonDates('VIX Index', fromDate, toDate, 'PX_LAST', VP.frequency, []);
#
#             % calculate logaritmic returns
#             spxPrices     = spxPricesTimeseries(:,2);
#             spxReturns    = log( spxPrices(2:end) ./ spxPrices(1:end-1) ); % ln(Si/Si-1)
#             spxDates      = spxPricesTimeseries(2:end, 1);                 % skip first date
#             VP.spxReturnsTimeseries = [spxDates, spxReturns];
#         end
#
#         function CalculateVolatilityOfSPX(VP, volWindowSize)
#             % volWindowSize = B
#             % volatility of S&P using volWindowSize day rolling window.
#
#             spxDates   = VP.spxReturnsTimeseries(:,1);
#             spxReturns = VP.spxReturnsTimeseries(:,2);
#
#             spxVol = nan(size(spxReturns));
#
#             for i = volWindowSize:length(spxReturns) % for example: 1:2 will be saved as volatility(2) -> we use close prices
#                 indices = (i-volWindowSize+1) : i;
#                 returnsInWindow = spxReturns(indices);
#                 spxVol(i) = Annualise( std(returnsInWindow), VP.frequency );
#             end
#
#             VP.spxVolTimeseries = [spxDates, spxVol];
#         end
#
#         function CalculateIndicator(VP, indicatorWindowSize)
#             % indicatorWindowSize - is an integer. indicatorWindowSize >= 2
#             % indicator = indicatorWindowSize day average of (VIX - (volWindowSize day historial vol of SPX * 100))
#
#             vixTimeseries         = VP.vixPricesTimeseries;
#             realisedVolTimeseries = VP.spxVolTimeseries;
#
#             % find data points corresponding to latest values.
#             % latest values are at the end of the timeseries
#             vixSeriesLen = size(vixTimeseries,1);
#             spxSeriesLen = size(realisedVolTimeseries,1);
#
#             % the indices correspond to last indicatorWindowSize elements in the timeseries
#             vixIndices = (vixSeriesLen - indicatorWindowSize + 1) : vixSeriesLen;
#             spxIndices = (spxSeriesLen - indicatorWindowSize + 1) : spxSeriesLen;
#
#             % extract dates to check if they correspond to the same elements
#             vixDates = vixTimeseries(vixIndices, 1);
#             spxDates = realisedVolTimeseries(spxIndices, 1);
#             % should contain only values equal to 1
#             comparisionResult = vixDates == spxDates;
#             if not(all(comparisionResult))
#                 errorMessage = 'ERROR: dates for VIX and volatility of S&P 500 are not equal';
#                 disp(errorMessage)
#                 throw(MException('CalculateIndicator:incorrectDates', errorMessage));
#             end
#
#             % if dates match than take the values
#             vixPrices   = vixTimeseries(vixIndices, 2);
#             realisedVol = realisedVolTimeseries(spxIndices, 2);
#
#             % finally, calculate value of the indicator for the next day
#             % VIX is in %, vol is expressed as a number so multiply by 100
#             diff = vixPrices - (realisedVol * 100);
#             VP.indicatorValue = VP.averageFunction(diff);
#         end
#
#         function [message, allocation] = CalculateSignal(VP, threshold, maxVixLevel)
#             % invest in VXX or XIV depending on the indicator and threshold
#             % the signal should be used to invest the following day
#
#             % threshold   - is a value that corresponds to indicator.
#             % maxVixLevel - is a maximum level of VIX Index. If VIX is above this level we go to cash.
#             % message     - is a text representation of the strategy signal
#             % allocation  - is a vector  allocation(1) corresponds to VXX (VIX ), allocation(2) corresponds to XIV (Inverse VIX)
#
#             indicator       = VP.indicatorValue;
#             currentVixPrice = VP.vixPricesTimeseries(end, 2);
#
#             % check if we can trade based on VIX Index level.
#             if currentVixPrice <= maxVixLevel
#
#                 if  indicator >= threshold
#                     % 'Normal' situation: Implied volatility is above realised
#                     % Invest in Inverse VIX (XIV)
#
#                     allocation(1) = 0;     % VXX
#                     allocation(2) = 1;     % XIV
#                     message = 'Go Long XIV (Inverse VIX)';
#                 elseif indicator < threshold
#                     % Realised Volatility spikes, invest in VIX Index (VXX)
#
#                     allocation(1) = 1;     % VXX
#                     allocation(2) = 0;     % XIV
#                     message = 'Go Long VXX (VIX)';
#                 else % indicator is NaN
#                     message = 'ERROR: Indicator is NaN';
#                     disp(message)
#                     throw(MException('CalculateSignal:incorrectIndicator',errorMessage));
#                 end
#
#                 message = sprintf('%s \r\nindicator = % 5.2f, threshold = % 5.2f',message, indicator, threshold);
#
#             else % stay in cash because VIX is to high
#                 allocation(1) = 0;     % VXX
#                 allocation(2) = 0;     % XIV
#                 message = 'Close the positions and go to cash. VIX Index is above the limit';
#             end
#
#         end
#
#         function stopLoss = CalculateStopLoss(VP, nrOfDaysOfVIX, stopLossParameter, maxStopLoss)
#             % stopLoss = max [ (-0.22) * sqrt( 20D MA(VIX) * 20 std(VIX) ), -3]
#             % stopLoss is expressed in % and refears to the previous close or open price is reallocation
#
#             vixPrices = VP.vixPricesTimeseries(:,2);
#             startingIndex = length(vixPrices) - nrOfDaysOfVIX + 1;
#
#             selectedVixPrices  = vixPrices(startingIndex:end);
#             selectedVixReturns = PricesToReturns(selectedVixPrices);
#             meanPrice          = mean(selectedVixPrices);
#             volatility         = std(selectedVixReturns);
#
#             stopLoss = stopLossParameter * sqrt(meanPrice * volatility);
#             stopLoss = max([stopLoss, maxStopLoss]);
#         end
#
#
#     end
#
# end
#
