class BrokerException(Exception):
    """
    Exception thrown when a Broker's operation fails.
    """
    pass


class OrderCancellingException(BrokerException):
    """
    Order couldn't be cancelled (e.g. because there was no Order of that id in the list of awaiting Orders
    or the request to cancel it timed-out).
    """
    pass
