from nose.tools import assert_raises

from rosidl_parser import *


def test_parse_primitive_value_string_invalid():
    with assert_raises(ValueError):
        parse_primitive_value_string(Type('pkg/Foo'), '')
    with assert_raises(ValueError):
        parse_primitive_value_string(Type('bool[]'), '')


def test_parse_primitive_value_string_bool():
    valid_bool_string_values = {
        'true': True,
        'TrUe': True,
        'TRUE': True,
        '1': True,
        'false': False,
        'FaLsE': False,
        'FALSE': False,
        '0': False,
    }
    for string_value, expected_value in valid_bool_string_values.items():
        value = parse_primitive_value_string(Type('bool'), string_value)
        assert value == expected_value

    with assert_raises(InvalidValue):
        parse_primitive_value_string(Type('bool'), '5')
    with assert_raises(InvalidValue):
        parse_primitive_value_string(Type('bool'), 'true ')


def test_parse_primitive_value_string_integer():
    integer_types = {
        'byte': [8, True],
        'char': [8, False],
        'int8': [8, False],
        'uint8': [8, True],
        'int16': [16, False],
        'uint16': [16, True],
        'int32': [32, False],
        'uint32': [32, True],
        'int64': [64, False],
        'uint64': [64, True],
    }
    for integer_type, (bits, is_unsigned) in integer_types.items():
        lower_bound = 0 if is_unsigned else -(2 ** (bits - 1))
        upper_bound = (2 ** (bits if is_unsigned else (bits - 1))) - 1

        value = parse_primitive_value_string(
            Type(integer_type), str(lower_bound))
        assert value == lower_bound
        value = parse_primitive_value_string(
            Type(integer_type), str(0))
        assert value == 0
        value = parse_primitive_value_string(
            Type(integer_type), str(upper_bound))
        assert value == upper_bound

        with assert_raises(InvalidValue):
            parse_primitive_value_string(
                Type(integer_type), 'value')
        with assert_raises(InvalidValue):
            parse_primitive_value_string(
                Type(integer_type), str(lower_bound - 1))
        with assert_raises(InvalidValue):
            parse_primitive_value_string(
                Type(integer_type), str(upper_bound + 1))


def test_parse_primitive_value_string_float():
    for float_type in ['float32', 'float64']:
        value = parse_primitive_value_string(
            Type(float_type), '0')
        assert value == 0
        value = parse_primitive_value_string(
            Type(float_type), '0.0')
        assert value == 0
        value = parse_primitive_value_string(
            Type(float_type), '3.14')
        assert value == 3.14

        with assert_raises(InvalidValue):
            parse_primitive_value_string(
                Type(float_type), 'value')


def test_parse_primitive_value_string_string():
    value = parse_primitive_value_string(
        Type('string'), 'foo')
    assert value == 'foo'

    value = parse_primitive_value_string(
        Type('string'), '"foo"')
    assert value == 'foo'

    value = parse_primitive_value_string(
        Type('string'), "'foo'")
    assert value == 'foo'

    value = parse_primitive_value_string(
        Type('string'), '"\'foo\'"')
    assert value == "'foo'"

    value = parse_primitive_value_string(
        Type('string'), '"foo ')
    assert value == '"foo '

    value = parse_primitive_value_string(
        Type('string<=3'), 'foo')
    assert value == 'foo'

    with assert_raises(InvalidValue):
        parse_primitive_value_string(
            Type('string<=3'), 'foobar')


def test_parse_primitive_value_string_unknown():
    class CustomType(Type):
        def is_primitive_type(self):
            return True
    type_ = CustomType('pkg/Foo')

    with assert_raises(AssertionError):
        parse_primitive_value_string(type_, '')
