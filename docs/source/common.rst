common
**********

enums
======
.. currentmodule:: qf_lib.common.enums
.. autosummary::	
	:nosignatures:
	:toctree: _autosummary
	:template: short_class.rst
	
	aggregations.Aggregation
	expiration_date_field.ExpirationDateField
	frequency.Frequency
	price_field.PriceField
	trade_field.TradeField

exceptions
============
.. currentmodule:: qf_lib.common.exceptions
.. autosummary::	
	:nosignatures:
	:toctree: _autosummary
	:template: short_class.rst
	
	broker_exceptions.BrokerException
	broker_exceptions.OrderCancellingException
	future_contracts_exceptions.NoValidTickerException

risk_parity_boxes
==================
.. currentmodule:: qf_lib.common.risk_parity_boxes.risk_parity_boxes
.. autosummary::	
	:nosignatures:
	:toctree: _autosummary
	:template: short_class.rst
	
	ChangeDirection
	RiskParityBoxes
	RiskParityBoxesFactory

tickers
==========
.. currentmodule:: qf_lib.common.tickers.tickers
.. autosummary::	
	:nosignatures:
	:toctree: _autosummary
	:template: short_class.rst
	
	Ticker
	BloombergTicker
	InternalDBTicker
	HaverTicker
	QuandlTicker
	CcyTicker
	
	
timeseries_analysis
=====================
.. currentmodule:: qf_lib.common.timeseries_analysis
.. autosummary::	
	:nosignatures:
	:toctree: _autosummary
	:template: short_class.rst
	
	return_attribution_analysis.ReturnAttributionAnalysis
	risk_contribution_analysis.RiskContributionAnalysis
	
utils
======

Classes
----------
.. currentmodule:: qf_lib.common.utils
.. autosummary::	
	:nosignatures:
	:toctree: _autosummary
	:template: short_class.rst
	
	confidence_interval.analytical_cone_base.AnalyticalConeBase
	confidence_interval.analytical_cone.AnalyticalCone
	confidence_interval.analytical_cone_oos.AnalyticalConeOOS

	dateutils.date_format.DateFormat
	dateutils.timer.Timer	
	dateutils.timer.RealTimer
	dateutils.timer.SettableTimer
	
	factorization.data_models.data_model.DataModel
	factorization.data_models.data_model_input.DataModelInput
	factorization.data_models.rolling_window_estimation.RollingWindowsEstimator
	factorization.data_presenters.data_presenter.DataPresenter
	factorization.data_presenters.rolling_data_presenter.RollingDataPresenter
	factorization.factors_identification.elastic_net_factors_identifier.ElasticNetFactorsIdentifier
	factorization.factors_identification.elastic_net_factors_identifier_simplified.ElasticNetFactorsIdentifierSimplified
	factorization.factors_identification.stepwise_factor_identifier.StepwiseFactorsIdentifier
	factorization.manager.FactorizationManager
	miscellaneous.consecutive_duplicates.Method
	returns.is_return_stats.InSampleReturnStats
	volatility.drift_independent_volatility.DriftIndependentVolatility
	volatility.volatility_forecast.VolatilityForecast
	volatility.volatility_manager.VolatilityManager
	data_cleaner.DataCleaner
	
Functions
-----------
.. currentmodule:: qf_lib.common.utils
.. autosummary::	
	:nosignatures:
	:toctree: _autosummary
	:template: function.rst
	
	close_open_gap.close_open_gap.close_open_gap
	dateutils.common_start_and_end.get_common_start_and_end
	dateutils.date_to_string.date_to_str
	dateutils.get_quarter.get_quarter
	dateutils.get_values_common_dates.get_values_for_common_dates
	dateutils.iso_to_gregorian.iso_to_gregorian
	dateutils.string_to_date.str_to_date
	dateutils.to_days.to_days
	miscellaneous.annualise_with_sqrt.annualise_with_sqrt
	miscellaneous.average_true_range.average_true_range
	miscellaneous.consecutive_duplicates.drop_consecutive_duplicates
	miscellaneous.function_name.get_function_name
	miscellaneous.kelly.kelly
	miscellaneous.kelly.kelly_binary
	miscellaneous.periods_list.periods_list_from_bool_series
	miscellaneous.to_list_conversion.convert_to_list
	miscellaneous.volume_weighted_average_price.volume_weighted_average_price
	numberutils.is_finite_number.is_finite_number
	ratios.calmar_ratio.calmar_ratio
	ratios.gain_to_pain_ratio.gain_to_pain_ratio
	ratios.information_ratio.information_ratio
	ratios.omega_ratio.omega_ratio
	ratios.sharpe_ratio.sharpe_ratio
	ratios.sorino_ratio.sorino_ratio
	returns.annualise_total_return.annualise_total_return
	returns.avg_drawdown.avg_drawdown
	returns.avg_drawdown_duration.avg_drawdown_duration
	returns.beta_and_alpha.beta_and_alpha_full_stats
	returns.cagr.cagr
	returns.convert_dataframe_frequency.convert_dataframe_frequency
	returns.custom_returns_aggregating.aggregate_returns
	returns.cvar.cvar
	returns.drawdown_tms.drawdown_tms
	returns.get_aggregate_returns.get_aggregate_returns
	returns.index_grouping.get_grouping_for_frequency
	returns.list_longest_drawdowns.list_longest_drawdowns
	returns.list_of_max_drawdowns.list_of_max_drawdowns
	returns.log_to_simple_return.log_to_simple_return
	returns.max_drawdown.max_drawdown
	returns.return_distribution_helpers.get_cone_chart
	returns.return_distribution_helpers.generate_random_paths
	returns.return_distribution_helpers.generate_random_log_paths
	returns.simple_to_log_return.simple_to_log_return
	returns.sqn.sqn
	returns.sqn.sqn_for100trades
	returns.sqn.avg_nr_of_trades_per1y
	returns.sqn.trade_based_cagr
	returns.sqn.trade_based_max_drawdown
	returns.tail_events.tail_events
	technical_analysis.utils.ta_series
	volatility.get_volatility.get_volatility
	volatility.intraday_volatility.intraday_volatility
	volatility.rolling_volatility.rolling_volatility
	