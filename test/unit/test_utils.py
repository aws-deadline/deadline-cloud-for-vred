# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Tests for utility functions and classes used throughout VRED submitter."""
import pytest
from unittest.mock import patch
import os
import yaml
from yaml.parser import ParserError

from vred_submitter.utils import (
    NamedValue,
    DynamicKeyNamedValueObject,
    DynamicKeyValueObject,
    timed_func,
    ceil,
    get_yaml_contents,
    is_number,
    is_all_numbers,
    is_numerically_defined,
    iterator_value,
    bool_to_str,
    clamp,
    get_normalized_path,
    is_valid_filename,
    get_file_name_path_components,
)


class TestNamedValue:
    """Test NamedValue class for named value objects."""

    def test_init(self):
        nv = NamedValue("test_name", 42)
        assert nv.__name__ == "test_name"
        assert nv.value == 42

    def test_repr(self):
        nv = NamedValue("test_name", 42)
        assert repr(nv) == "NamedValue(name='test_name', value='42')"

    def test_eq_with_named_value(self):
        nv1 = NamedValue("test1", 42)
        nv2 = NamedValue("test2", 42)
        nv3 = NamedValue("test3", 43)
        assert nv1 == nv2
        assert nv1 != nv3

    def test_eq_with_other_value(self):
        nv = NamedValue("test", 42)
        assert nv == 42
        assert nv != 43


class TestDynamicKeyNamedValueObject:
    def test_init(self):
        data = {"key1": "value1", "key2": 42}
        obj = DynamicKeyNamedValueObject(data)

        assert hasattr(obj, "key1")
        assert hasattr(obj, "key2")
        assert obj.key1.value == "value1"
        assert obj.key2.value == 42
        assert obj.key1.__name__ == "key1"
        assert obj.key2.__name__ == "key2"


class TestDynamicKeyValueObject:
    def test_init(self):
        data = {"key1": "value1", "key2": 42}
        obj = DynamicKeyValueObject(data)

        assert hasattr(obj, "key1")
        assert hasattr(obj, "key2")
        assert obj.key1 == "value1"
        assert obj.key2 == 42


class TestTimedFunc:
    @patch("vred_submitter.utils.print")
    def test_timed_func(self, mock_print):
        @timed_func
        def test_function(a, b, c=3):
            return a + b + c

        result = test_function(1, 2, c=4)

        assert result == 7
        # The timed_func decorator should call print
        mock_print.assert_called_once()


class TestCeil:
    def test_ceil_positive(self):
        assert ceil(1.234, 2) == 1.24
        assert ceil(1.235, 2) == 1.24
        assert ceil(1.236, 2) == 1.24
        assert ceil(1.999, 1) == 2.0

    def test_ceil_negative(self):
        assert ceil(-1.234, 2) == -1.23
        assert ceil(-1.235, 2) == -1.23
        assert ceil(-1.236, 2) == -1.23

    def test_ceil_zero(self):
        assert ceil(0.0, 2) == 0.0

    def test_ceil_invalid_decimals(self):
        with pytest.raises(TypeError):
            ceil(1.23, 2.5)

        with pytest.raises(ValueError):
            ceil(1.23, 0)

        with pytest.raises(ValueError):
            ceil(1.23, -1)

    def test_ceil_invalid_number(self):
        with pytest.raises(TypeError):
            ceil("1.23", 2)


class TestGetYamlContents:
    """Test YAML file loading and validation."""

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.open")
    @patch("yaml.safe_load")
    def test_valid_yaml(self, mock_safe_load, mock_open, mock_is_file):
        mock_is_file.return_value = True
        mock_file = mock_open.return_value.__enter__.return_value
        mock_safe_load.return_value = {"key": "value"}

        result = get_yaml_contents("test.yaml")

        mock_is_file.assert_called_once()
        mock_safe_load.assert_called_once_with(mock_file)
        assert result == {"key": "value"}

    @patch("pathlib.Path.is_file")
    def test_file_not_found(self, mock_is_file):
        mock_is_file.return_value = False

        with pytest.raises(FileNotFoundError, match="File not found"):
            get_yaml_contents("nonexistent.yaml")

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.open")
    @patch("yaml.safe_load")
    def test_not_a_dict(self, mock_safe_load, mock_open, mock_is_file):
        mock_is_file.return_value = True
        mock_safe_load.return_value = ["list", "not", "dict"]

        with pytest.raises(TypeError, match="YAML file must contain a dictionary"):
            get_yaml_contents("test.yaml")

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.open")
    @patch("yaml.safe_load")
    def test_yaml_parser_error(self, mock_safe_load, mock_open, mock_is_file):
        mock_is_file.return_value = True
        mock_safe_load.side_effect = ParserError("Parser error")

        with pytest.raises(yaml.YAMLError):
            get_yaml_contents("test.yaml")

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.open")
    def test_permission_error(self, mock_open, mock_is_file):
        mock_is_file.return_value = True
        mock_open.side_effect = PermissionError("Permission denied")

        with pytest.raises(PermissionError):
            get_yaml_contents("test.yaml")

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.open")
    def test_general_error(self, mock_open, mock_is_file):
        mock_is_file.return_value = True
        mock_open.side_effect = Exception("General error")

        with pytest.raises(RuntimeError):
            get_yaml_contents("test.yaml")


class TestIsNumber:
    """Test numeric string validation."""

    def test_valid_numbers(self):
        assert is_number("123")
        assert is_number("123.456")
        assert is_number("-123")
        assert is_number("-123.456")
        assert is_number("0")
        assert is_number("0.0")
        assert is_number("1e10")

    def test_invalid_numbers(self):
        assert not is_number("")
        assert not is_number("abc")
        assert not is_number("123abc")
        assert not is_number("abc123")
        assert not is_number("123 456")
        assert not is_number(None)


class TestIsAllNumbers:
    def test_all_numbers(self):
        assert is_all_numbers(["123", "456", "789"])
        assert is_all_numbers(["123.456", "-789", "0"])

    def test_not_all_numbers(self):
        assert not is_all_numbers(["123", "abc", "789"])
        assert not is_all_numbers(["123", "", "789"])
        assert not is_all_numbers([])
        assert not is_all_numbers(["123", None, "789"])


class TestIsNumericallyDefined:
    def test_numerically_defined(self):
        assert is_numerically_defined("123")
        assert is_numerically_defined("123.456")
        assert is_numerically_defined("-123")
        assert is_numerically_defined("0")

    def test_not_numerically_defined(self):
        assert not is_numerically_defined("")
        assert not is_numerically_defined("abc")
        assert not is_numerically_defined("inf")
        assert not is_numerically_defined("-inf")
        assert not is_numerically_defined("NaN")
        assert not is_numerically_defined("nan")


class TestIteratorValue:
    def test_iterator_value(self):
        class MockIterator:
            def __init__(self, value):
                self.value = value

            def __reduce__(self):
                return (MockIterator, (self.value,))

        iterator = MockIterator(42)
        assert iterator_value(iterator) == 42


class TestBoolToStr:
    def test_bool_to_str(self):
        assert bool_to_str(True) == "true"
        assert bool_to_str(False) == "false"


class TestClamp:
    def test_clamp_within_range(self):
        assert clamp(5, 1, 10) == 5
        assert clamp(5.5, 1.0, 10.0) == 5.5

    def test_clamp_below_min(self):
        assert clamp(0, 1, 10) == 1
        assert clamp(0.5, 1.0, 10.0) == 1.0

    def test_clamp_above_max(self):
        assert clamp(11, 1, 10) == 10
        assert clamp(11.5, 1.0, 10.0) == 10.0

    def test_clamp_type_preservation(self):
        # Test basic type preservation
        assert isinstance(clamp(5, 1, 10), int)
        assert isinstance(clamp(5.0, 1.0, 10.0), float)


class TestGetNormalizedPath:
    """Test path normalization utility."""

    def test_normal_path(self):
        assert get_normalized_path("/path/to/file") == os.path.normpath("/path/to/file")
        assert get_normalized_path("C:\\path\\to\\file") == os.path.normpath("C:\\path\\to\\file")

    def test_empty_path(self):
        assert get_normalized_path("") == ""
        assert get_normalized_path(None) == ""

    def test_dot_path(self):
        assert get_normalized_path(".") == ""


class TestIsValidFilename:
    """Test filename validation for invalid characters."""

    def test_valid_filenames(self):
        assert is_valid_filename("file.txt")
        assert is_valid_filename("my_file-123.doc")
        assert is_valid_filename("file123")

    def test_invalid_filenames(self):
        assert not is_valid_filename("file/name.txt")
        assert not is_valid_filename("file\\name.txt")
        assert not is_valid_filename("file:name.txt")
        assert not is_valid_filename("file?name.txt")
        assert not is_valid_filename("file*name.txt")
        assert not is_valid_filename("file|name.txt")
        assert not is_valid_filename("file<name.txt")
        assert not is_valid_filename("file>name.txt")


class TestGetFileNamePathComponents:
    def test_normal_path(self):
        directory, filename, extension = get_file_name_path_components("/path/to/file.txt")
        assert directory == os.path.normpath("/path/to")
        assert filename == "file"
        assert extension == "txt"

    @pytest.mark.skipif(os.name != "nt", reason="Windows-specific path test")
    def test_windows_path(self):
        directory, filename, extension = get_file_name_path_components("C:\\path\\to\\file.txt")
        assert directory == os.path.normpath("C:\\path\\to")
        assert filename == "file"
        assert extension == "txt"

    def test_filename_only(self):
        directory, filename, extension = get_file_name_path_components("file.txt")
        assert directory == ""
        assert filename == "file"
        assert extension == "txt"

    def test_no_extension(self):
        directory, filename, extension = get_file_name_path_components("/path/to/file")
        assert directory == os.path.normpath("/path/to")
        assert filename == "file"
        assert extension == ""

    def test_empty_path(self):
        directory, filename, extension = get_file_name_path_components("")
        assert directory == ""
        assert filename == ""
        assert extension == ""
