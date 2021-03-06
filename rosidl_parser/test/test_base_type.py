from nose.tools import assert_raises

from rosidl_parser import *


def test_base_type_constructor():
    primitive_types = [
        'bool',
        'byte',
        'char',
        'float32',
        'float64',
        'int8',
        'uint8',
        'int16',
        'uint16',
        'int32',
        'uint32',
        'int64',
        'uint64',
        'string']
    for primitive_type in primitive_types:
        base_type = BaseType(primitive_type)
        assert base_type.pkg_name is None
        assert base_type.type == primitive_type
        assert base_type.string_upper_bound is None

    base_type = BaseType('string<=23')
    assert base_type.pkg_name is None
    assert base_type.type == 'string'
    assert base_type.string_upper_bound == 23

    with assert_raises(TypeError):
        BaseType('string<=upperbound')
    with assert_raises(TypeError):
        BaseType('string<=0')

    base_type = BaseType('pkg/Msg')
    assert base_type.pkg_name == 'pkg'
    assert base_type.type == 'Msg'
    assert base_type.string_upper_bound is None

    base_type = BaseType('Msg', 'pkg')
    assert base_type.pkg_name == 'pkg'
    assert base_type.type == 'Msg'
    assert base_type.string_upper_bound is None

    with assert_raises(InvalidResourceName):
        BaseType('Foo')

    with assert_raises(InvalidResourceName):
        BaseType('pkg name/Foo')

    with assert_raises(InvalidResourceName):
        BaseType('pkg/Foo Bar')


def test_base_type_methods():
    assert BaseType('bool').is_primitive_type()
    assert not BaseType('pkg/Foo').is_primitive_type()

    assert BaseType('bool') != 23

    assert BaseType('pkg/Foo') == BaseType('pkg/Foo')
    assert BaseType('bool') != BaseType('pkg/Foo')

    {BaseType('bool'): None}

    assert str(BaseType('pkg/Foo')) == 'pkg/Foo'
    assert str(BaseType('bool')) == 'bool'
    assert str(BaseType('string<=5')) == 'string<=5'
