import os
import re

PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR = '/'
COMMENT_DELIMITER = '#'
CONSTANT_SEPARATOR = '='
ARRAY_UPPER_BOUND_TOKEN = '<='
STRING_UPPER_BOUND_TOKEN = '<='

PRIMITIVE_TYPES = [
    'bool',
    'byte',
    'char',
    # TODO reconsider wchar
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
    'string',
    # TODO reconsider wstring / u16string / u32string
    # TODO duration and time
    'duration',  # for compatibility only
    'time',  # for compatibility only
]

VALID_PACKAGE_NAME_PATTERN = re.compile('^[a-z][a-z0-9_]*$')
# TODO replace relaxed patterns used for compatibility
# VALID_FIELD_NAME_PATTERN = re.compile('^[a-z][a-z0-9_]*$')
VALID_FIELD_NAME_PATTERN = re.compile('^[A-Za-z][A-Za-z0-9_]*$')
# TODO replace relaxed patterns used for compatibility
# VALID_MESSAGE_NAME_PATTERN = re.compile('^[A-Z][A-Za-z0-9]*$')
VALID_MESSAGE_NAME_PATTERN = re.compile('^[A-Za-z][A-Za-z0-9]*$')
VALID_CONSTANT_NAME_PATTERN = re.compile('^[A-Z][A-Z0-9_]*$')


class InvalidMessageSpecification(Exception):
    pass


class InvalidResourceName(InvalidMessageSpecification):
    pass


class InvalidFieldDefinition(InvalidMessageSpecification):
    pass


class UnknownMessageType(InvalidMessageSpecification):
    pass


class InvalidValue(Exception):

    def __init__(self, type_, value_string, message_suffix=None):
        message = "value '%s' can not be converted to type '%s'" % \
            (value_string, type_)
        if message_suffix is not None:
            message += ': %s' % message_suffix
        super(InvalidValue, self).__init__(message)


def is_valid_package_name(name):
    try:
        m = VALID_PACKAGE_NAME_PATTERN.match(name)
    except TypeError:
        raise InvalidResourceName(name)
    return m is not None and m.group(0) == name


def is_valid_field_name(name):
    try:
        m = VALID_FIELD_NAME_PATTERN.match(name)
    except TypeError:
        raise InvalidResourceName(name)
    return m is not None and m.group(0) == name


def is_valid_message_name(name):
    try:
        m = VALID_MESSAGE_NAME_PATTERN.match(name)
    except TypeError:
        raise InvalidResourceName(name)
    return m is not None and m.group(0) == name


def is_valid_constant_name(name):
    try:
        m = VALID_CONSTANT_NAME_PATTERN.match(name)
    except TypeError:
        raise InvalidResourceName(name)
    return m is not None and m.group(0) == name


class BaseType(object):

    __slots__ = ['pkg_name', 'type', 'string_upper_bound']

    def __init__(self, type_string, context_package_name=None):
        # check for primitive types
        if type_string in PRIMITIVE_TYPES:
            self.pkg_name = None
            self.type = type_string
            self.string_upper_bound = None

        elif type_string.startswith('string%s' % STRING_UPPER_BOUND_TOKEN):
            self.pkg_name = None
            self.type = 'string'
            upper_bound_string = type_string[len(self.type) +
                                             len(STRING_UPPER_BOUND_TOKEN):]

            ex = TypeError(("the upper bound of the string type '%s' must " +
                            "be a valid integer value > 0") % type_string)
            try:
                self.string_upper_bound = int(upper_bound_string)
            except ValueError:
                raise ex
            if self.string_upper_bound <= 0:
                raise ex

        else:
            # split non-primitive type information
            parts = type_string.split(PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR)
            if not (len(parts) == 2 or
                    (len(parts) == 1 and context_package_name is not None)):
                raise InvalidResourceName(type_string)

            if len(parts) == 2:
                # either the type string contains the package name
                self.pkg_name = parts[0]
                self.type = parts[1]
            else:
                # or the package name is provided by context
                self.pkg_name = context_package_name
                self.type = type_string
            if not is_valid_package_name(self.pkg_name):
                raise InvalidResourceName(self.pkg_name)
            if not is_valid_message_name(self.type):
                raise InvalidResourceName(self.type)
            self.string_upper_bound = None

    def is_primitive_type(self):
        return self.pkg_name is None

    def __eq__(self, other):
        if other is None or not isinstance(other, BaseType):
            return False
        return self.pkg_name == other.pkg_name and \
            self.type == other.type and \
            self.string_upper_bound == other.string_upper_bound

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        if self.pkg_name is not None:
            return '%s/%s' % (self.pkg_name, self.type)

        s = self.type
        if self.string_upper_bound:
            s += '%s%u' % \
                (STRING_UPPER_BOUND_TOKEN, self.string_upper_bound)
        return s


class Type(BaseType):

    __slots__ = ['is_array', 'array_size', 'is_upper_bound']

    def __init__(self, type_string, context_package_name=None):
        # check for array brackets
        self.is_array = type_string[-1] == ']'

        self.array_size = None
        self.is_upper_bound = False
        if self.is_array:
            try:
                index = type_string.rindex('[')
            except ValueError:
                raise TypeError("the type ends with ']' but does not " +
                                "contain a '['" % type_string)
            array_size_string = type_string[index + 1:-1]
            # get array limit
            if array_size_string != '':

                # check if the limit is an upper bound
                self.is_upper_bound = array_size_string.startswith(
                    ARRAY_UPPER_BOUND_TOKEN)
                if self.is_upper_bound:
                    array_size_string = array_size_string[
                        len(ARRAY_UPPER_BOUND_TOKEN):]

                ex = TypeError((
                    "the size of array type '%s' must be a valid integer " +
                    "value > 0 optionally prefixed with '%s' if it is only " +
                    "an upper bound") %
                    (ARRAY_UPPER_BOUND_TOKEN, type_string))
                try:
                    self.array_size = int(array_size_string)
                except ValueError:
                    raise ex
                # check valid range
                if self.array_size <= 0:
                    raise ex

            type_string = type_string[:index]

        super(Type, self).__init__(
            type_string,
            context_package_name=context_package_name)

    def __eq__(self, other):
        if other is None or not isinstance(other, Type):
            return False
        return super(Type, self).__eq__(other) and \
            self.is_array == other.is_array and \
            self.array_size == other.array_size and \
            self.is_upper_bound == other.is_upper_bound

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        s = super(Type, self).__str__()
        if self.is_array:
            s += '['
            if self.is_upper_bound:
                s += ARRAY_UPPER_BOUND_TOKEN
            if self.array_size is not None:
                s += '%u' % self.array_size
            s += ']'
        return s


class Constant(object):

    __slots__ = ['primitive_type', 'name', 'value']

    def __init__(self, primitive_type, name, value_string):
        if primitive_type not in PRIMITIVE_TYPES:
            raise TypeError("the constant type '%s' must be a primitive type" %
                            primitive_type)
        self.primitive_type = primitive_type
        if not is_valid_constant_name(name):
            raise NameError("the constant name '%s' is not valid" % name)
        self.name = name
        if value_string is None:
            raise ValueError("the constant value must not be 'None'")

        self.value = parse_primitive_value_string(
            Type(primitive_type), value_string)

    def __eq__(self, other):
        if other is None or not isinstance(other, Constant):
            return False
        return self.primitive_type == other.primitive_type and \
            self.name == other.name and \
            self.value == other.value

    def __str__(self):
        value = self.value
        if self.primitive_type == 'string':
            value = "'%s'" % value
        return '%s %s=%s' % (self.primitive_type, self.name, value)


class Field(object):

    def __init__(self, type_, name, default_value_string=None):
        if not isinstance(type_, Type):
            raise TypeError(
                "the field type '%s' must be a 'Type' instance" % type_)
        self.type = type_
        if not is_valid_field_name(name):
            raise NameError("the field name '%s' is not valid" % name)
        self.name = name
        if default_value_string is None:
            self.default_value = None
        else:
            self.default_value = parse_value_string(
                type_, default_value_string)

    def __eq__(self, other):
        if other is None or not isinstance(other, Field):
            return False
        else:
            return self.type == other.type and \
                self.name == other.name and \
                self.default_value == other.default_value

    def __str__(self):
        s = '%s %s' % (str(self.type), self.name)
        if self.default_value is not None:
            if self.type.is_primitive_type() and not self.type.is_array and \
                    self.type.type == 'string':
                s += " '%s'" % self.default_value
            else:
                s += ' %s' % self.default_value
        return s


class MessageSpecification(object):

    def __init__(self, pkg_name, msg_name, fields, constants):
        self.base_type = BaseType(
            pkg_name + PACKAGE_NAME_MESSAGE_TYPE_SEPARATOR + msg_name)

        self.fields = []
        for index, field in enumerate(fields):
            if not isinstance(field, Field):
                raise TypeError("field %u must be a 'Field' instance" % index)
            self.fields.append(field)
        # ensure that there are no duplicate field names
        field_names = [f.name for f in self.fields]
        duplicate_field_names = set([n for n in field_names
                                     if field_names.count(n) > 1])
        if duplicate_field_names:
            raise ValueError(
                'the fields iterable contains duplicate names: %s' %
                ', '.join(sorted(duplicate_field_names)))

        self.constants = []
        for index, constant in enumerate(constants):
            if not isinstance(constant, Constant):
                raise TypeError("constant %u must be a 'Constant' instance" %
                                index)
            self.constants.append(constant)
        # ensure that there are no duplicate constant names
        constant_names = [c.name for c in self.constants]
        duplicate_constant_names = set([n for n in constant_names
                                        if constant_names.count(n) > 1])
        if duplicate_constant_names:
            raise ValueError(
                'the constants iterable contains duplicate names: %s' %
                ', '.join(sorted(duplicate_constant_names)))

    def __eq__(self, other):
        if not other or not isinstance(other, MessageSpecification):
            return False
        return self.base_type == other.base_type and \
            len(self.fields) == len(other.fields) and \
            self.fields == other.fields and \
            len(self.constants) == len(other.constants) and \
            self.constants == other.constants


def parse_message_file(pkg_name, interface_filename):
    basename = os.path.basename(interface_filename)
    msg_name = os.path.splitext(basename)[0]
    with open(interface_filename, 'r') as h:
        return parse_message_string(
            pkg_name, msg_name, h.read())


def parse_message_string(pkg_name, msg_name, message_string):
    fields = []
    constants = []

    lines = message_string.splitlines()
    for line in lines:
        # ignore whitespaces and comments
        line = line.strip()
        if not line:
            continue
        index = line.find(COMMENT_DELIMITER)
        if index == 0:
            continue
        if index != -1:
            line = line[:index]
            line = line.rstrip()

        type_string, _, rest = line.partition(' ')
        rest = rest.lstrip()
        if not rest:
            raise InvalidFieldDefinition(line)
        index = rest.find(CONSTANT_SEPARATOR)
        if index == -1:
            # line contains a field
            field_name, _, default_value_string = rest.partition(' ')
            default_value_string = default_value_string.lstrip()
            if not default_value_string:
                default_value_string = None
            fields.append(Field(
                Type(type_string, context_package_name=pkg_name),
                field_name, default_value_string))
        else:
            # line contains a constant
            name, _, value = rest.partition(CONSTANT_SEPARATOR)
            name = name.rstrip()
            value = value.lstrip()
            constants.append(Constant(type_string, name, value))

    return MessageSpecification(pkg_name, msg_name, fields, constants)


def parse_value_string(type_, value_string):
    if type_.is_primitive_type() and not type_.is_array:
        return parse_primitive_value_string(type_, value_string)

    if type_.is_primitive_type() and type_.is_array and type_.type != 'string':
        # check for array brackets
        if not value_string.startswith('[') or not value_string.endswith(']'):
            raise InvalidValue(
                type_, value_string,
                "array value must start with '[' and end with ']'")
        elements_string = value_string[1:-1]

        # split on separator and check size constraints
        value_strings = elements_string.split(',') if elements_string else []
        if type_.array_size:
            # check for exact size
            if not type_.is_upper_bound and \
                    len(value_strings) != type_.array_size:
                raise InvalidValue(
                    type_, value_string,
                    'array must have exactly %u elements, not %u' %
                    (type_.array_size, len(value_strings)))
            # check for upper bound
            if type_.is_upper_bound and len(value_strings) > type_.array_size:
                raise InvalidValue(
                    type_, value_string,
                    'array must have not more than %u elements, not %u' %
                    (type_.array_size, len(value_strings)))

        # parse all primitive values one by one
        values = []
        for index, element_string in enumerate(value_strings):
            element_string = element_string.strip()
            try:
                base_type = Type(BaseType.__str__(type_))
                value = parse_primitive_value_string(base_type, element_string)
            except InvalidValue as e:
                raise InvalidValue(
                    type_, value_string, 'element %u with %s' % (index, e))
            values.append(value)
        return values

    raise NotImplementedError(
        "parsing string values into type '%s' is not supported" % type_)


def parse_primitive_value_string(type_, value_string):
    if not type_.is_primitive_type() or type_.is_array:
        raise ValueError('the passed type must be a non-array primitive type')
    primitive_type = type_.type

    if primitive_type == 'bool':
        true_values = ['true', '1']
        false_values = ['false', '0']
        if value_string.lower() not in (true_values + false_values):
            raise InvalidValue(
                primitive_type, value_string,
                "must be either 'true' / '1' or 'false' / '0'")
        return value_string.lower() in true_values

    if primitive_type == 'byte':
        # same as uint8
        ex = InvalidValue(primitive_type, value_string,
                          'must be a valid integer value >= 0 and <= 255')
        try:
            value = int(value_string)
        except ValueError:
            raise ex
        if value < 0 or value > 255:
            raise ex
        return value

    if primitive_type == 'char':
        # same as int8
        ex = InvalidValue(primitive_type, value_string,
                          'must be a valid integer value >= -128 and <= 127')
        try:
            value = int(value_string)
        except ValueError:
            raise ex
        if value < -128 or value > 127:
            raise ex
        return value

    if primitive_type in ['float32', 'float64']:
        try:
            return float(value_string)
        except ValueError:
            raise InvalidValue(
                primitive_type, value_string,
                "must be a floating point number using '.' as the separator")

    if primitive_type in [
        'int8', 'uint8',
        'int16', 'uint16',
        'int32', 'uint32',
        'int64', 'uint64',
    ]:
        # determine lower and upper bound
        is_unsigned = primitive_type.startswith('u')
        bits = int(primitive_type[4 if is_unsigned else 3:])
        lower_bound = 0 if is_unsigned else -(2 ** (bits - 1))
        upper_bound = (2 ** (bits if is_unsigned else (bits - 1))) - 1

        ex = InvalidValue(primitive_type, value_string,
                          'must be a valid integer value >= %d and <= %u' %
                          (lower_bound, upper_bound))

        try:
            value = int(value_string)
        except ValueError:
            raise ex

        # check that value is in valid range
        if value < lower_bound or value > upper_bound:
            raise ex

        return value

    if primitive_type == 'string':
        # remove outer quotes to allow leading / trailing spaces in the string
        for quote in ['"', "'"]:
            if value_string.startswith(quote) and value_string.endswith(quote):
                value_string = value_string[1:-1]
                break

        # check that value is in valid range
        if type_.string_upper_bound and \
                len(value_string) > type_.string_upper_bound:
            base_type = Type(BaseType.__str__(type_))
            raise InvalidValue(
                base_type, value_string,
                'string must not exceed the maximum length of %u characters' %
                type_.string_upper_bound)

        return value_string

    assert False, "unknown primitive type '%s'" % primitive_type


def validate_field_types(spec, known_msg_types):
    for field in spec.fields:
        if field.type.is_primitive_type():
            continue
        base_type = BaseType(BaseType.__str__(field.type))
        if base_type not in known_msg_types:
            raise UnknownMessageType(str(field))
