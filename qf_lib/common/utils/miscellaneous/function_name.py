import sys


def get_function_name(parent_idx=0) -> str:
    """
    While called inside a function or a class method it
    returns the name of the function/method that called it as a string.

    example:
    def method_a(self):
        ...
        get_function_name()  # returns 'method_a'
    """
    return sys._getframe(1 + parent_idx).f_code.co_name
