class PascalTypeException(Exception):
    pass


# Note: if you change the size of integer from 4 bytes to something else, these constants need to change
MAXINT = 2147483647
NEGATIVE_MAXINT = -1 * MAXINT
MAXINT_AS_STRING = str(MAXINT)
NEGATIVE_MAXINT_AS_STRING = str(NEGATIVE_MAXINT)


def is_integer_or_subrange_of_integer(pascal_type):
    if isinstance(pascal_type, IntegerType):
        return True
    elif isinstance(pascal_type, SubrangeType) and isinstance(pascal_type.host_type, IntegerType):
        return True
    else:
        return False


class BaseType:
    def __init__(self, identifier, denoter=None):
        # denoter may be None but may also be a BaseType.  For example:
        #
        # type
        #   x = integer;
        #   c = x;
        #
        # type x would be an IntegerType() with identifier x and denoter None.
        # type c would be an IntegerType() with identifier c and denoter the type object of x.
        assert isinstance(identifier, str)
        assert denoter is None or isinstance(denoter, BaseType)

        self.size = 0
        self.identifier = identifier.lower()
        self.denoter = denoter

    def is_string_type(self):
        return False

    def get_pointer_to(self):
        # returns a new pointer type that is a pointer to the current type
        return PointerType("_pointer_to_{}".format(self.identifier), self)

    def __str__(self):
        return self.identifier

    def __repr__(self):  # pragma: no cover
        return "Type '{}' with denoter {}".format(self.identifier, repr(self.denoter))

    # allows us to use Types in Symbol tables, and yet keep the vocabulary in the Type such that it matches
    # the terminology in the ISO standard
    @property
    def name(self):
        return self.identifier


class SimpleType(BaseType):
    pass


class OrdinalType(SimpleType):
    def __init__(self, identifier, denoter=None):
        super().__init__(identifier, denoter)

    def __getitem__(self, n):  # pragma: no cover
        # this is a pure virtual function
        # returns the item in the Nth position in the sequence defined by the ordinal type.
        raise NotImplementedError("__getitem__() not implemented")

    def position(self, s):  # pragma: no cover
        # this is a pure virtual function
        # returns the position where item S is in the sequence defined by the ordinal type
        raise NotImplementedError("position() not implemented)")

    def min_item(self):  # pragma: no cover
        # this is a pure virtual function
        # returns the smallest possible value of the type, as a string
        raise NotImplementedError("min_item() not implemented")

    def max_item(self):  # pragma: nocover
        # this is a pure virtual function
        # returns the largest possible value of the type, as a string
        raise NotImplementedError("max_item() not implemented")


class IntegerType(OrdinalType):
    def __init__(self, identifier="integer", denoter=None):
        super().__init__(identifier, denoter)
        self.size = 4

    def __getitem__(self, n):  # pragma: no cover
        assert isinstance(n, int)
        assert n <= MAXINT
        assert n >= NEGATIVE_MAXINT
        return str(n)

    def position(self, s):
        if isinstance(s, str):
            s = int(s)
        assert isinstance(s, int)
        assert s <= MAXINT
        assert s >= NEGATIVE_MAXINT
        return s

    def min_item(self):
        return NEGATIVE_MAXINT_AS_STRING

    def max_item(self):
        return MAXINT_AS_STRING


class CharacterType(OrdinalType):
    def __init__(self, identifier="char", denoter=None):
        super().__init__(identifier, denoter)
        self.size = 1

    def __getitem__(self, n):  # pragma: no cover
        assert isinstance(n, int)
        assert n >= 0
        assert n <= 255
        return chr(n)

    def position(self, s):
        assert isinstance(s, str)
        assert len(s) == 1
        return ord(s)

    def min_item(self):
        return chr(0)

    def max_item(self):
        return chr(255)


class BooleanType(OrdinalType):
    def __init__(self, identifier="boolean", denoter=None):
        super().__init__(identifier, denoter)
        self.size = 1

    def __getitem__(self, n):  # pragma: no cover
        assert n in (0, 1)
        return str(n)

    def position(self, s):
        assert s.lower() in ('false', 'true')
        if s.lower() == 'false':
            return 0
        else:
            return 1

    def min_item(self):
        return "false"

    def max_item(self):
        return "true"


class EnumeratedTypeValue:
    # needed so that the values can go into the symbol table
    def __init__(self, identifier, type_identifier, value):
        assert isinstance(identifier, str)
        assert isinstance(type_identifier, str)
        assert isinstance(value, int)
        assert value >= 0
        self.identifier = identifier
        self.type_identifier = type_identifier
        self.value = value

    # allows us to use EnumeratedTypeValues in Symbol tables, and yet keep the vocabulary in the TypeDefinition
    # such that matches the terminology in the ISO standard
    @property
    def name(self):
        return self.identifier

    def __str__(self):  # pragma: no cover
        return self.identifier

    def __repr__(self):  # pragma: no cover
        return "ID:{} for Type:{} with value:{}".format(self.identifier, self.identifier, self.value)


class EnumeratedType(OrdinalType):
    def __init__(self, identifier, value_list, denoter=None):
        i = 0
        value_identifier_list = []
        while i < len(value_list):
            assert isinstance(value_list[i], EnumeratedTypeValue)
            assert value_list[i].type_identifier == identifier
            assert value_list[i].value == i
            # cannot define the same constant multiple times in the same type
            assert value_list[i].identifier not in value_identifier_list
            value_identifier_list.append(value_list[i].identifier)
            i += 1

        super().__init__(identifier, denoter)
        if len(value_list) > 255:
            error_str = "Enumerated type '{}' has {} identifiers.  Maximum is 255."
            error_str = error_str.format(identifier, str(len(value_list)))
            raise PascalTypeException(error_str)
        self.size = 1
        self.value_list = value_list

    def __str__(self):  # pragma: no cover
        return "Enumerated type: {}".format(self.identifier)

    def __repr__(self):  # pragma: no cover
        return_str = "Enumerated type: {} with values (".format(self.identifier)
        for i in self.value_list:
            return_str = return_str + str(i) + ', '
        return_str = return_str[:-2] + ')'
        return return_str

    def __getitem__(self, n):  # pragma: no cover
        assert isinstance(n, int)
        assert n >= 0
        assert n < len(self.value_list)
        return self.value_list[n]

    def position(self, s):
        assert isinstance(s, str)  # EnumeratedTypes contain list of strings
        i = 0
        found_it = False
        while i < len(self.value_list) and not found_it:
            if self.value_list[i].identifier.lower() == s.lower():
                found_it = True
            else:
                i += 1
        if not found_it:  # pragma: no cover
            # side note - this error is caught upstream by checking the types, so I cannot come up with a
            # coverage scenario for this.
            error_str = "'{}' is not a valid value for enumerated type '{}'"
            error_str = error_str.format(s, self.identifier)
            raise PascalTypeException(error_str)
        return i

    def min_item(self):
        return self.value_list[0].identifier

    def max_item(self):
        return self.value_list[-1].identifier


class SubrangeType(OrdinalType):
    def __init__(self, identifier, host_type, range_min, range_max, denoter=None):
        assert isinstance(host_type, OrdinalType)
        super().__init__(identifier, denoter)
        self.size = host_type.size
        self.host_type = host_type
        self.range_min = range_min  # these are always strings
        self.range_max = range_max
        # need to convert the range_min / range_max to ints so we can compare them
        self.range_min_int = self.host_type.position(self.range_min)
        self.range_max_int = self.host_type.position(self.range_max)
        if self.range_min_int > self.range_max_int:
            # required in 6.4.2.4
            error_str = "Invalid subrange - value {} is not less than or equal to value {}"
            error_str = error_str.format(self.range_min, self.range_max)
            raise PascalTypeException(error_str)

    def __getitem__(self, n):  # pragma: no cover
        assert self.range_min_int + n <= self.range_max_int
        return self.host_type[n - self.range_min_int]

    def position(self, s):
        assert self.is_in_range(s)
        host_position = self.host_type.position(s)
        return host_position - self.range_min_int

    def is_in_range(self, s):
        host_position = self.host_type.position(s)
        return self.range_min_int <= host_position <= self.range_max_int

    def __str__(self):  # pragma: no cover
        return "Subrange type: '{}'".format(self.identifier)

    def __repr__(self):  # pragma: no cover
        return_str = "Subrange type: '{}'.  Host_typedef: {} \n range_min: {}  range_max: {}"
        return_str = return_str.format(self.identifier, repr(self.host_type), self.range_min, self.range_max)
        return_str += "\nrange_min_int: {}  range_max_int: {}".format(str(self.range_min_int), str(self.range_max_int))
        return return_str

    def min_item(self):
        return self.range_min

    def max_item(self):
        return self.range_max


class RealType(SimpleType):
    def __init__(self, identifier="real", denoter=None):
        super().__init__(identifier, denoter)
        self.size = 8


class PointerType(BaseType):
    def __init__(self, identifier, points_to_type, denoter=None):
        assert isinstance(points_to_type, BaseType)
        super().__init__(identifier, denoter)

        self.size = 8
        self.points_to_type = points_to_type


class StructuredType(BaseType):
    def __init__(self, identifier, denoter=None):
        super().__init__(identifier, denoter)
        self.is_packed = False  # TODO handle packed structures


class ArrayType(StructuredType):
    def __init__(self, identifier, index_type, component_type, is_packed, denoter=None):
        assert isinstance(index_type, OrdinalType)
        assert isinstance(component_type, BaseType)
        assert isinstance(is_packed, bool)

        super().__init__(identifier, denoter)
        self.index_type = index_type
        self.component_type = component_type
        self.is_packed = is_packed

        self.index_min = self.index_type.min_item()  # just like Subranges, these are always strings
        self.index_max = self.index_type.max_item()
        # need to convert the range min / range max to ints so we can compare them
        self.index_min_int = self.index_type.position(self.index_min)
        self.index_max_int = self.index_type.position(self.index_max)
        self.num_items_in_array = (self.index_max_int - self.index_min_int) + 1

        self.size = self.num_items_in_array * self.component_type.size

    def is_string_type(self):
        # 6.4.3.2 of the ISO standard states that a string type must be packed, have an index type
        # that is an integer subrange that has 1 as its smallest value and a number greater than 1 as its largest
        # value, and it's component-type is a denotation of the char type.
        if self.is_packed and isinstance(self.index_type, SubrangeType) and \
                isinstance(self.index_type.host_type, IntegerType) and \
                self.index_min == "1" and self.num_items_in_array >= 2 and \
                isinstance(self.component_type, CharacterType):
            return True
        else:
            return False

    def __repr__(self):  # pragma: no cover
        return_str = ""
        if self.is_packed:
            return_str = "Packed "
        return_str += "Array [{}] of {} (size {} bytes)".format(repr(self.index_type), repr(self.component_type),
                                                                self.size)
        return_str += "\n BaseType size: {}".format(self.component_type.size)
        if self.is_string_type():
            return_str += "\nString Type"
        return return_str


class RecordType(StructuredType):
    pass


class SetType(StructuredType):
    pass


class FileType(StructuredType):
    def __init__(self, identifier, component_type, denoter=None):
        assert isinstance(component_type, BaseType)
        # cannot have a File of Files.
        assert not isinstance(component_type, FileType)
        super().__init__(identifier, denoter)
        self.component_type = component_type
        # FileType layout = 8 bytes for the FILE* followed by 1 byte for the "mode-type."
        # mode-type = 0 : file not initialized
        # mode-type = 1 : generation
        # mode-type = 2 : inspection
        self.size = 9 + self.component_type.size

    def __str__(self):  # pragma: no cover
        return "file of {}".format(self.component_type.identifier)


class TextFileType(FileType):
    def __init__(self, identifier="text", denoter=None):
        # for now, a text file will be a typedef of chars
        super().__init__(identifier, CharacterType(), denoter)


class ActivationType(BaseType):
    pass


class ProcedureType(ActivationType):
    def __init__(self, identifier="procedure activation", denoter=None):
        super().__init__(identifier, denoter)


class FunctionType(ActivationType):
    def __init__(self, identifier="function activation", denoter=None):
        super().__init__(identifier, denoter)


class StringLiteralType(BaseType):
    # this is a bit hacky, but allows us to pass around string literals in places that require pascal types
    # pascal literals never have spaces, so the user can never create a type
    # named "_string literal" to cause an issue with this type.  Needs to have the
    # leading underscore because compatibility functions strip off the "literal" at the
    # end to get the base type's identifier, so _string literal will become _string.
    # _string has a leading underscore for reasons described elsewhere.

    def __init__(self):
        super().__init__("_string literal")
        self.size = 8
