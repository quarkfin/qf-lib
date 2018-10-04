import datetime as dt

from arch.univariate.volatility import GARCH

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.common.utils.volatility.volatility_forecast import VolatilityForecast
from .import_from_excel import import_data

frequency = Frequency.DAILY
path = r'./sectors.xlsx'
simple_ret_df, weights = import_data(frequency, path)


returns = simple_ret_df['ENERGY']
split_date = dt.datetime(2014, 1, 1)
forecast_horizon = 10

# vol_process = ARCH(p=p)
# vol_process = GARCH(p=p, o=o, q=q, power=power)
# vol_process = EGARCH(p=p, o=o, q=q)
# vol_process = HARCH(lags=p)

vol_forecast = VolatilityForecast(returns)
vol_process = GARCH()
forcasted_value = vol_forecast.calculate_vol_forecast(vol_process, forecast_horizon, method='analytic')

print('Forecasted volatility: {}'.format(forcasted_value))
print('Forecasted annualised volatility: {}'.format(annualise_with_sqrt(forcasted_value,frequency)))
