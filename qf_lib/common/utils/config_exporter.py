import inspect
from collections import defaultdict
from enum import Enum
from typing import Dict


class ConfigExporter:

    _config_details = defaultdict(dict)

    @classmethod
    def update_config(cls, func):
        """
        Helper function, used to decorate a function, in order to facilitate config saving and export. In case of
        calling the decorated function multiple times only the last call is saved.
        For the given function func(arg1, arg2) in case of calling func(val1, val2) the following will be saved to the
        _config_details dictionary: "module_with_func": {"func": {"arg1": "val1", "arg2": "val2"}}.
        """

        def wrapped_function(*args, **kwargs):

            function_name = func.__name__
            args_dict = dict(inspect.signature(func).bind_partial(*args).arguments)
            arguments_dict = {**args_dict, **kwargs}

            object_for_func = arguments_dict.pop('self', None)
            function_origin = object_for_func.__class__.__name__ if object_for_func is not None else func.__module__
            cls._config_details[function_origin][function_name] = arguments_dict

            return func(*args, **kwargs)

        return wrapped_function

    @classmethod
    def append_config(cls, func):
        """
        Helper function, used to decorate a function, in order to facilitate config saving and export. In case of
        calling the decorated function multiple times each call is saved.
        For the given function func(arg1, arg2) in case of calling func(val1, val2) and then func(val3, val4) the
        following will be saved to the _config_details dictionary:
        "module_with_func": {"func": [{"arg1": "val1", "arg2": "val2"}, {"arg1": "val3", "arg2": "val4"}]}.
        """

        def wrapped_function(*args, **kwargs):

            function_name = func.__name__
            args_dict = dict(inspect.signature(func).bind_partial(*args).arguments)
            arguments_dict = {**args_dict, **kwargs}

            object_for_func = arguments_dict.pop('self', None)
            function_origin = object_for_func.__class__.__name__ if object_for_func is not None else func.__module__

            if function_name in cls._config_details[function_origin].keys():
                cls._config_details[function_origin][function_name].append(arguments_dict)
            else:
                cls._config_details[function_origin][function_name] = [arguments_dict]

            return func(*args, **kwargs)

        return wrapped_function

    @classmethod
    def get_formatted_config(cls, places: int = 3):
        def format_value(value):
            if isinstance(value, Enum):
                formatted_value = value.name
            elif isinstance(value, dict):
                formatted_value = {k: format_value(value[k]) for k in value.keys()}
            elif isinstance(value, (list, tuple, set)):
                val_type = type(value)
                formatted_value = val_type(format_value(v) for v in value)
            elif isinstance(value, float):
                formatted_value = "{:,.{}f}".format(value, places)
            else:
                try:
                    formatted_value = value.__name__
                except AttributeError:
                    formatted_value = str(value)

            return formatted_value

        formatted_config = {k: format_value(v) for k, v in cls._config_details.items()}
        return formatted_config

    @classmethod
    def clear_config(cls):
        cls._config_details = defaultdict(dict)

    @classmethod
    def print_config(cls, file=None):
        def print_config(d: Dict, file, indent=0):
            for key, value in d.items():
                if isinstance(value, dict):
                    print(" " * indent + "{}:".format(key), file=file)
                    print_config(value, file, indent=indent+2)
                    print(file=file)
                else:
                    print(" " * indent + "{}: {}".format(key, value), file=file)

        formatted_config = cls.get_formatted_config()
        print_config(formatted_config, file)
