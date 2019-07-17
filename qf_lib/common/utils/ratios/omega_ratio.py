from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def omega_ratio(returns_tms: SimpleReturnsSeries, threshold: float = 0) -> float:
    """
    Omega Ratio - The Omega Ratio is a measure of performance that doesn't assume a normal distribution of returns.
    The Omega ratio is a relative measure of the likelihood of achieving a given return, such as a minimum
    acceptable return (MAR) or a target return. The higher the omega value, the greater the probability that a given
    return will be met or exceeded. Omega represents a ratio of the cumulative probability of an investment's
    outcome above an investor's defined return level (a threshold level), to the cumulative probability
    of an investment's outcome below an investor's threshold level. The omega concept divides expected returns into
    two parts – gains and losses, or returns above the expected rate (the upside)and those below it (the downside).
    Therefore, in simple terms, consider omega as the ratio of upside returns (good) relative to downside returns
    (bad).

    Parameters
    ----------
    returns_tms
        time series of price returns
    threshold
        threshold (e.g. benchmark return or target return) for the portfolio

    Returns
    -------
    omega_ratio
        Omega Ratio calculated for threshold
    """
    returns_tms = returns_tms.to_simple_returns()
    downside = 0
    upside = 0

    for ret in returns_tms.values:
        if ret < threshold:
            downside += threshold - ret
        else:
            upside += ret - threshold

    return upside / downside
