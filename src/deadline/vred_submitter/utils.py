# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""General Convenience/Utility Functions"""

import math
import os
import re
import time
import yaml

from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Tuple, TypeVar, Union
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from .constants import Constants

TypeName = TypeVar("TypeName")


class StrEnum(str, Enum):
    """
    This is a backport of Python 3.11's StrEnum for compatibility with Python 3.10.
    """

    def __new__(cls, value):
        if not isinstance(value, str):
            raise TypeError(f"{cls.__name__} members must be strings")
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj

    def __str__(self):
        return str(self.value)

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list) -> str:
        return name.lower()


class NamedValue:
    """
    Wrapper class to store a value along with its name.
    It allows primitive values (which don't normally have a __name__ attribute) to store their identifier name.
    """

    def __init__(self, name: str, value: Any) -> None:
        """
        Initialize a NamedValue instance.
        param: name : the name to associate with the value.
        param: value : the value to be wrapped.
        """
        self.value = value
        self.__name__ = name

    def __repr__(self) -> str:
        """
        Returns a string representation of the NamedValue instance.
        return: a string containing both a name and a value.
        """
        return f"NamedValue(name='{self.__name__}', value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """
        Compares this NamedValue with another value for equality.
        param: other: the value to compare
        return: True if the values are equal, False otherwise.
        """
        if isinstance(other, NamedValue):
            return self.value == other.value
        return self.value == other


class DynamicKeyNamedValueObject:
    def __init__(self, data_dict: Dict[str, Any]) -> None:
        """
        Assigns attributes and values to this object that reflect the contents of data_dict and provides support for
        getting the names of primitives
        param: data_dict: attributes/properties and associated values
        """
        for k, v in data_dict.items():
            named_value = NamedValue(name=k, value=v)
            setattr(self, k, named_value)


class DynamicKeyValueObject:
    def __init__(self, data_dict: Dict[str, Any]) -> None:
        """
        Assigns attributes and values to this object; reflect the contents of data_dict for easy attribute-based access.
        :param: data_dict: attributes/properties and values
        """
        for k, v in data_dict.items():
            setattr(self, k, v)


def timed_func(func: Callable[..., TypeName]) -> Callable[..., TypeName]:
    """
    Decorator that wraps a function for deducing performance timing
    param: func: the function to be timed
    return: wrapped function that prints timing information when called
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        print(
            f"func: {func.__name__} with args: {args}, kwargs: {kwargs}, took {elapsed:.3f} seconds"
        )
        return result

    return wrapped


def ceil(number: float, decimals: int) -> float:
    """Rounds a number up to a specific decimal place.
    param: number: the number to round up
    param: decimals: the number of decimal places to round
    raise: TypeError: if decimals isn't an integer
    raise: ValueError: if decimals is negative
    return: rounded number.
    """
    if not isinstance(decimals, int) or not isinstance(number, float):
        raise TypeError
    if decimals <= 0:
        raise ValueError()
    return math.ceil(number * (Constants.BASE_TEN**decimals)) / (Constants.BASE_TEN**decimals)


def get_yaml_contents(file_path: str) -> Dict[str, Any]:
    """
    Read and parse contents of a YAML file.
    param: file_path: path to the YAML file as string or Path object
    raise: FileNotFoundError: If the specified file does not exist
    raise: PermissionError: If the program lacks permission to read the file
    raise: yaml.YAMLError: If the YAML content is malformed
    raise: TypeError: If the YAML content is not a dictionary
    return: parsed YAML contents
    """
    try:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"{Constants.ERROR_YAML_NOT_FOUND}: {file_path}")
        with path.open(Constants.READ_FLAG, encoding=Constants.UTF8_FLAG) as file_handle:
            contents = yaml.safe_load(file_handle)
        if not isinstance(contents, dict):
            raise TypeError(f"{Constants.ERROR_YAML_OBJECT_NOT_FOUND}: {type(contents)}")
        return contents
    except (ParserError, ScannerError) as yaml_err:
        raise yaml.YAMLError(
            f"{Constants.ERROR_YAML_INVALID_FORMAT} {file_path}: {str(yaml_err)}"
        ) from yaml_err
    except FileNotFoundError as error:
        raise FileNotFoundError(f"{Constants.ERROR_FILE_NOT_FOUND} {file_path}") from error
    except TypeError:
        raise
    except PermissionError as error:
        raise PermissionError(
            f"{Constants.ERROR_FILE_ACCESS_PERMISSION_DENIED} {file_path}"
        ) from error
    except Exception as exc:
        raise RuntimeError(
            f"{Constants.ERROR_YAML_UNEXPECTED_ERROR} {file_path}: {str(exc)}"
        ) from exc


def is_number(string: str) -> bool:
    """
    Check if the provided string represents a number.
    param: string: the string to check
    return: True if the string represents a number, False otherwise
    """
    if not string:
        return False
    try:
        float(string)
    except (ValueError, TypeError):
        return False
    return True


def is_all_numbers(strings: List[str]) -> bool:
    """
    Check if all provided strings represent numbers.
    param: strings: list of strings to check
    return: true if all provided strings represent numbers.
    """
    if not strings:
        return False
    for string in strings:
        if not is_number(string):
            return False
    return True


def is_numerically_defined(num: str) -> bool:
    """
    Check if the provided string represents a numerically defined value.
    param: num: the numeric string to evaluate
    return: True if the string represents a numerically defined value; False otherwise
    """
    if not is_number(num):
        return False

    value = float(num)
    return not (math.isinf(value) or math.isnan(value))


def iterator_value(counter: Iterator[int]) -> int:
    """
    Get the current value of an iterator counter.
    param: counter: iterator counter
    return: the current integral value of an iterator counter
    """
    return int(counter.__reduce__()[1][0])


def bool_to_str(boolean: bool) -> str:
    """
    Convert a boolean value to its string representation.
    param: boolean: boolean value to convert
    return: "false" if boolean==False; else "true"
    """
    return str(boolean).lower()


def clamp(
    value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]
) -> Union[int, float]:
    """
    Clamp a numeric value to be between (or at) min and max values, preserving the original type.
    param: value: value to clamp
    param: min_val: minimum value accepted
    param: max_val: maximum value accepted
    return: clamped value
    """
    result = max(min_val, min(value, max_val))
    if isinstance(value, int) and isinstance(min_val, int) and isinstance(max_val, int):
        return int(result)
    return result


def get_normalized_path(path: str) -> str:
    """
    return: empty path if path is None/empty/".", else normalized absolute path
    """
    return os.path.normpath(path) if str(path) != "." and path else ""


def is_valid_filename(filename: str) -> bool:
    """
    return: True if filename consists of characters comprising a valid filename; False otherwise
    """
    return bool(re.match(Constants.FILENAME_UNICODE_REGEX, filename, re.UNICODE))


def get_file_name_path_components(filename_with_path: str) -> Tuple[str, str, str]:
    """
    Extracts the directory, filename prefix, and extension from filename_with_path.
    param: filename_with_path: path to examine
    return: the directory, filename prefix, and extension
    """
    if not filename_with_path:
        return "", "", ""
    directory = get_normalized_path(os.path.dirname(filename_with_path))
    filename_prefix = os.path.splitext(os.path.basename(filename_with_path))[0]
    extension = os.path.splitext(filename_with_path)[1][1:]
    return directory, filename_prefix, extension
