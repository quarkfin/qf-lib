
class TimeseriesAnalysisDTO(object):
    def __init__(self):
        self.frequency                 = None
        self.start_date                = None
        self.end_date                  = None

        self.total_return              = None
        self.cagr                      = None       # Compounded Annual Growth Rate = (End/Begining)^(1/#ofYeares)–1
        self.annualised_vol            = None
        self.annualised_upside_vol     = None
        self.annualised_downside_vol   = None

        self.sharpe_ratio              = None
        self.omega_ratio               = None
        self.calmar_ratio              = None
        self.gain_to_pain_ratio        = None
        self.sorino_ratio              = None

        self.cvar                      = None        # 5% CVaR expressed related to the specified frequency
        self.annualised_cvar           = None        # annualised 5% CVaR
        self.max_drawdown              = None        # maximum drawdown
        self.avg_drawdown              = None        # average of the whole underwater chart
        self.avg_drawdown_duration     = None        # average duration of a drawdown

        self.best_return               = None
        self.worst_return              = None
        self.avg_positive_return       = None
        self.avg_negative_return       = None
        self.skewness                  = None
        self.kurtosis                  = None
        self.kelly                     = None

