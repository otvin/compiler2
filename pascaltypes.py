class PascalTypeException(Exception):
    pass


# Note: if you change the size of integer from 4 bytes to something else, these constants need to change
MAXINT = 2147483647
NEGMAXINT = -1 * MAXINT
STRMAXINT = str(MAXINT)
STRNEGMAXINT = str(NEGMAXINT)

def is_integer_or_subrange_of_integer(pascaltype):
    if isinstance(pascaltype, IntegerType):
        return True
    elif isinstance(pascaltype, SubrangeType) and isinstance(pascaltype.hosttype, IntegerType):
        return True
    else:
        return False

class BaseType:
    def __init__(self, identifier, denoter=None):
        # denoter may be None but may also be a BaseType.  For example:
        #
        # type
        #   i = integer;
        #   c = i;
        #
        # type i would be an IntegerType() with identifier i and denoter None.
        # type c would be an IntegerType() with identifier c and denoter the type object of i.
        assert isinstance(identifier, str)
        assert denoter is None or isinstance(denoter, BaseType)

        self.size = 0
        self.identifier = identifier.lower()
        self.denoter = denoter

    def is_string_type(self):
        return False

    def get_pointer_to(self):
        # returns a new pointertype that is a pointer to the current type
        return PointerType("_ptrto_{}".format(self.identifier), self)

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

    def __getitem__(self, n): # pragma: no cover
        assert isinstance(n, int)
        assert n <= MAXINT
        assert n >= NEGMAXINT
        return str(n)

    def position(self, s):
        if isinstance(s, str):
            s = int(s)
        assert isinstance(s, int)
        assert s <= MAXINT
        assert s >= NEGMAXINT
        return s

    def min_item(self):
        return STRNEGMAXINT

    def max_item(self):
        return STRMAXINT


class CharacterType(OrdinalType):
    def __init__(self, identifier="char", denoter=None):
        super().__init__(identifier, denoter)
        self.size = 1

    def __getitem__(self, n): # pragma: no cover
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

    def __getitem__(self, n): # pragma: no cover
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
    def __init__(self, identifier, typeidentifier, value):
        assert isinstance(identifier, str)
        assert isinstance(typeidentifier, str)
        assert isinstance(value, int)
        assert value >= 0
        self.identifier = identifier
        self.typeidentifier = typeidentifier
        self.value = value

    # allows us to use EnumeratedTypeValues in Symbol tables, and yet keep the vocabulary in the TypeDefinition
    # such that matches the terminology in the ISO standard
    @property
    def name(self):
        return self.identifier

    def __str__(self): # pragma: no cover
        return self.identifier

    def __repr__(self): # pragma: no cover
        return "ID:{} for Type:{} with value:{}".format(self.identifier, self.identifier, self.value)


class EnumeratedType(OrdinalType):
    def __init__(self, identifier, value_list, denoter=None):
        i = 0
        value_identifier_list = []
        while i < len(value_list):
            assert isinstance(value_list[i], EnumeratedTypeValue)
            assert value_list[i].typeidentifier == identifier
            assert value_list[i].value == i
            # cannot define the same constant multiple times in the same type
            assert value_list[i].identifier not in value_identifier_list
            value_identifier_list.append(value_list[i].identifier)
            i += 1

        super().__init__(identifier, denoter)
        if len(value_list) > 255:
            errstr = "Enumerated type '{}' has {} identifiers.  Maximum is 255."
            errstr = errstr.format(identifier, str(len(value_list)))
            raise PascalTypeException(errstr)
        self.size = 1
        self.value_list = value_list

    def __str__(self):  # pragma: no cover
        return "Enumerated type: {}".format(self.identifier)

    def __repr__(self):  # pragma: no cover
        ret = "Enumerated type: {} with values (".format(self.identifier)
        for i in self.value_list:
            ret = ret + str(i) + ', '
        ret = ret[:-2] + ')'
        return ret

    def __getitem__(self, n): # pragma: no cover
        assert isinstance(n, int)
        assert n >= 0
        assert n < len(self.value_list)
        return self.value_list[n]

    def position(self, s):
        assert isinstance(s, str)  # EnumeratedTypes contain list of strings
        i = 0
        foundit = False
        while i < len(self.value_list) and not foundit:
            if self.value_list[i].identifier.lower() == s.lower():
                foundit = True
            else:
                i += 1
        if not foundit: # pragma: no cover
            # side note - this error is caught upstream by checking the types, so I cannot come up with a
            # coverage scenario for this.
            errstr = "'{}' is not a valid value for enumerated type '{}'"
            errstr = errstr.format(s, self.identifier)
            raise PascalTypeException(errstr)
        return i

    def min_item(self):
        return self.value_list[0].identifier

    def max_item(self):
        return self.value_list[-1].identifier


class SubrangeType(OrdinalType):
    def __init__(self, identifier, hosttype, rangemin, rangemax, denoter=None):
        assert isinstance(hosttype, OrdinalType)
        super().__init__(identifier, denoter)
        self.size = hosttype.size
        self.hosttype = hosttype
        self.rangemin = rangemin  # these are always strings
        self.rangemax = rangemax
        # need to convert the rangemin / rangemax to ints so we can compare them
        self.rangemin_int = self.hosttype.position(self.rangemin)
        self.rangemax_int = self.hosttype.position(self.rangemax)
        if self.rangemin_int > self.rangemax_int:
            # required in 6.4.2.4
            errstr = "Invalid subrange - value {} is not less than or equal to value {}"
            errstr = errstr.format(self.rangemin, self.rangemax)
            raise PascalTypeException(errstr)

    def __getitem__(self, n): # pragma: no cover
        assert self.rangemin_int + n <= self.rangemax_int
        return self.hosttype[n - self.rangemin_int]

    def position(self, s):
        assert self.isinrange(s)
        host_position = self.hosttype.position(s)
        return host_position - self.rangemin_int

    def isinrange(self, s):
        host_position = self.hosttype.position(s)
        return self.rangemin_int <= host_position <= self.rangemax_int

    def __str__(self):  # pragma: no cover
        return "Subrange type: '{}'".format(self.identifier)

    def __repr__(self):  # pragma: no cover
        retstr = "Subrange type: '{}'.  Hosttypedef: {} \n rangemin: {}  rangemax: {}"
        retstr = retstr.format(self.identifier, repr(self.hosttype), self.rangemin, self.rangemax)
        retstr += "\nrangemin_int: {}  rangemax_int: {}".format(str(self.rangemin_int), str(self.rangemax_int))
        return retstr

    def min_item(self):
        return self.rangemin

    def max_item(self):
        return self.rangemax


class RealType(SimpleType):
    def __init__(self, identifier="real", denoter=None):
        super().__init__(identifier, denoter)
        self.size = 8


class PointerType(BaseType):
    def __init__(self, identifier, pointstotype, denoter=None):
        assert isinstance(pointstotype, BaseType)
        super().__init__(identifier, denoter)

        self.size = 8
        self.pointstotype = pointstotype


class StructuredType(BaseType):
    def __init__(self, identifier, denoter=None):
        super().__init__(identifier, denoter)
        self.ispacked = False  # TODO handle packed structures


class ArrayType(StructuredType):
    def __init__(self, identifier, indextype, componenttype, ispacked, denoter=None):
        assert isinstance(indextype, OrdinalType)
        assert isinstance(componenttype, BaseType)
        assert isinstance(ispacked, bool)

        super().__init__(identifier, denoter)
        self.indextype = indextype
        self.componenttype = componenttype
        self.ispacked = ispacked

        self.indexmin = self.indextype.min_item()  # just like Subranges, these are always strings
        self.indexmax = self.indextype.max_item()
        # need to convert the rangemin / rangemax to ints so we can compare them
        self.indexmin_int = self.indextype.position(self.indexmin)
        self.indexmax_int = self.indextype.position(self.indexmax)
        self.numitemsinarray = (self.indexmax_int - self.indexmin_int) + 1

        self.size = self.numitemsinarray * self.componenttype.size

    def is_string_type(self):
        # 6.4.3.2 of the ISO standard states that a string type must be packed, have an index type
        # that is an integer subrange that has 1 as its smallest value and a number greater than 1 as its largest
        # value, and it's component-type is a denotation of the char type.
        if self.ispacked and isinstance(self.indextype, SubrangeType) and \
                isinstance(self.indextype.hosttype, IntegerType) and \
                self.indexmin == "1" and self.numitemsinarray >= 2 and \
                isinstance(self.componenttype, CharacterType):
            return True
        else:
            return False

    def __repr__(self):  # pragma: no cover
        retstr = ""
        if self.ispacked:
            retstr = "Packed "
        retstr += "Array [{}] of {} (size {} bytes)".format(repr(self.indextype), repr(self.componenttype),
                                                            self.size)
        retstr += "\n basetype size: {}".format(self.componenttype.size)
        if self.is_string_type():
            retstr += "\nString Type"

        return retstr


class RecordType(StructuredType):
    pass


class SetType(StructuredType):
    pass


class FileType(StructuredType):
    def __init__(self, identifier, componenttype, denoter=None):
        assert isinstance(componenttype, BaseType)
        # cannot have a File of Files.
        assert not isinstance(componenttype, FileType)
        super().__init__(identifier, denoter)
        self.componenttype = componenttype
        # FileType layout = 8 bytes for the FILE* followed by 1 byte for the mode-type
        # mode-type = 0 : file not initialized
        # mode-type = 1 : generation
        # mode-type = 2 : inspection
        self.size = 9 + self.componenttype.size

    def __str__(self): # pragma: no cover
        return "file of {}".format(self.componenttype.identifier)


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
