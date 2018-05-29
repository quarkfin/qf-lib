from enum import Enum


class Aggregation(Enum):
    """
    List of aggregations used for reporting.
    """

    TOTAL_PORTFOLIO = "Total"

    ASIA_EQUITY = "Asia Equity"
    EM_EQUITY = "EM Equity"
    EUROPE_EQUITY = "Europe Equity"
    INTERNAL_EQUITY = "Internal Equity"
    NORTH_AMERICA_EQUITY = "North America Equity"

    def __init__(self, short_description: str):
        self.short_description = short_description
