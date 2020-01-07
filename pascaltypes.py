class PascalTypeException(Exception):
    pass


class BaseType:
    def __init__(self):
        self.size = 0
        self.typename = None

    def __str__(self):
        return self.typename


class StringLiteralType(BaseType):
    # this is a bit hacky, but allows us to pass around string literals in places that require pascal types
    def __init__(self):
        super().__init__()
        self.typename = "string literal"
        self.size = 8


class SimpleType(BaseType):
    pass


class OrdinalType(SimpleType):
    def __init__(self):
        super().__init__()

    def __getitem__(self, n):  # pragma: no cover
        # this is a pure virtual function
        # returns the item in the Nth position in the sequence defined by the ordinal type.
        raise NotImplementedError("__getitem__() not implemented")

    def position(self, s):  # pragma: no cover
        # this is a pure virtual function
        # returns the position where item S is in the sequence defined by the ordinal type
        raise NotImplementedError("position() not implemented)")


# Putting these constants here because if we change the size of the Integer, we would need to change
# the constants.
MAXINT = 2147483647
NEGMAXINT = -1 * MAXINT
STRMAXINT = str(MAXINT)
STRNEGMAXINT = str(NEGMAXINT)


class IntegerType(OrdinalType):
    def __init__(self):
        super().__init__()
        self.typename = "integer"
        self.size = 4

    def __getitem__(self, n):
        assert isinstance(n, int)
        assert n <= MAXINT
        assert n >= NEGMAXINT
        return n

    def position(self, s):
        assert isinstance(s, int)
        assert s <= MAXINT
        assert s >= NEGMAXINT
        return s


class CharacterType(OrdinalType):
    def __init__(self):
        super().__init__()
        self.typename = "char"
        self.size = 1

    def __getitem__(self, n):
        assert isinstance(n, int)
        assert n >= 0
        assert n <= 255
        return chr(n)

    def position(self, s):
        assert isinstance(s, str)
        assert len(s) == 1
        return ord(s)


class BooleanType(OrdinalType):
    def __init__(self):
        super().__init__()
        self.typename = "Boolean"
        self.size = 1

    def __getitem__(self, n):
        assert n in (0, 1)
        return n

    def position(self, s):
        assert s in (0, 1)
        return s


class EnumeratedTypeValue:
    # needed so that the values can go into the symbol table
    def __init__(self, identifier):
        self.identifier = identifier

    # allows us to use TypeDefinitions in Symbol tables, and yet keep the vocabluary in the TypeDefinition
    # such that matches the terminology in the ISO standard
    @property
    def name(self):
        return self.identifier


class EnumeratedType(OrdinalType):
    def __init__(self, typename, identifier_list):
        for i in identifier_list:
            assert isinstance(i, str)  # TODO - should these be identifiers?

        super().__init__()
        if len(identifier_list) > 255:
            errstr = "Enumerated type '{}' has {} identifiers.  Maximum is 255."
            errstr = errstr.format(typename, str(len(identifier_list)))
            raise PascalTypeException(errstr)
        self.typename = typename
        self.size = 1
        self.identifier_list = identifier_list

    def __str__(self):
        ret = "Enumerated type: {} with values (".format(self.typename)
        for i in self.identifier_list:
            ret = ret + i + ', '
        ret = ret[:-2] + ')'
        return ret

    def __getitem__(self, n):
        assert isinstance(n, int)
        assert n >= 0
        assert n < len(self.identifier_list)
        return self.identifier_list[n]

    def position(self, s):
        assert isinstance(s, str)  # EnumeratedTypes contain list of strings
        i = 0
        foundit = False
        while i < len(self.identifier_list) and not foundit:
            if self.identifier_list[s].lower() == s.lower():
                foundit = True
            else:
                i += 1
        if not foundit:
            errstr = "'{}' is not a valid value for enumerated type '{}'"
            errstr = errstr.format(s, self.typename)
            raise PascalTypeException(errstr)
        return i


class SubrangeType(OrdinalType):
    def __init__(self, typename, hosttype, rangemin, rangemax):
        assert isinstance(hosttype, OrdinalType)
        super().__init__()
        self.typename = typename
        self.size = 4
        self.hosttype = hosttype
        self.rangemin = rangemin  # min/max will be int for Integer, Char, Boolean, and strings for EnumeratedTypes
        self.rangemax = rangemax

    def __getitem__(self, n):
        min_inhosttype = self.hosttype.position(self.rangemin)
        max_inhosttype = self.hosttype.position(self.rangemax)
        assert min_inhosttype + n <= max_inhosttype
        return self.hosttype[n - min_inhosttype]

    def position(self, s):
        host_position = self.hosttype.position(s)
        min_inhosttype = self.hosttype.position(self.rangemin)
        max_inhosttype = self.hosttype.position(self.rangemax)
        assert host_position >= min_inhosttype
        assert host_position <= max_inhosttype
        return host_position - min_inhosttype


class RealType(SimpleType):
    def __init__(self):
        super().__init__()
        self.typename = "real"
        self.size = 8


class PointerType(BaseType):
    def __init__(self, pointstotype):
        assert isinstance(pointstotype, BaseType)
        super().__init__()
        self.typename = "pointer"
        self.size = 8
        self.pointstotype = pointstotype


class StructuredType(BaseType):
    def __init__(self):
        super().__init__()
        self.ispacked = False  # TODO handle packed structures


class ArrayType(StructuredType):
    # TODO: minindex and maxindex can be values of any OrdinalType, not just integers
    # Do we convert those values to integers during compilation?  Probably?
    def __init__(self, typename, arrayoftype, dimensionlist):
        assert isinstance(arrayoftype, BaseType)

        super().__init__()
        self.typename = typename
        self.arrayoftype = arrayoftype
        self.dimensionlist = dimensionlist

        numitemsinarray = 1
        for i in dimensionlist:
            assert isinstance(i, SubrangeType)
            numitemsindimension = i.position(i.rangemax) - i.position(i.rangemin)
            numitemsinarray *= numitemsindimension

        self.size = numitemsinarray * arrayoftype.size


class StringType(ArrayType):
    # def __init__(self, maxindex):
    #    # super().__init__(CharacterType(), 1, maxindex)
    #    # self.ispacked = True
    #    # self.typename = "string"
    pass


class RecordType(StructuredType):
    pass


class SetType(StructuredType):
    pass


class FileType(StructuredType):
    pass


class ActivationType(BaseType):
    pass


class ProcedureType(ActivationType):
    def __init__(self):
        super().__init__()
        self.typename = "procedure activation"


class FunctionType(ActivationType):
    def __init__(self):
        super().__init__()
        self.typename = "function activation"


class TypeDef:
    # Denoter may be a basetype but doesn't have to be.  For example:
    # type
    #   i=integer;
    #   c=i;
    #
    # the typedefinition for i would be identifier = 'i', denoter = IntegerType()
    # and basetype = IntegerType().
    # the typedefinition for j would be identifier = 'j' denoter = the TypeDefinition of i,
    # and basetype = IngeterType().

    def __init__(self, identifier, denoter, basetype):
        assert isinstance(denoter, TypeDef) or isinstance(denoter, BaseType)
        assert isinstance(basetype, BaseType)
        self.identifier = identifier.lower()
        self.denoter = denoter
        self.basetype = basetype

    # allows us to use TypeDefs in Symbol tables, and yet keep the vocabluary in the TypeDef
    # such that matches the terminology in the ISO standard
    @property
    def name(self):
        return self.identifier

    def __str__(self):
        return "TypeDef '{}'".format(self.name)

    def __repr__(self):
        ret = "TypeDef '{}' with denoter {} and basetype {}"
        ret = ret.format(self.name, str(self.denoter), str(self.basetype))
        return ret


SIMPLETYPEDEF_INTEGER = TypeDef("integer", IntegerType(), IntegerType())
SIMPLETYPEDEF_BOOLEAN = TypeDef("boolean", BooleanType(), BooleanType())
SIMPLETYPEDEF_REAL = TypeDef("real", RealType(), RealType())
SIMPLETYPEDEF_CHAR = TypeDef("char", CharacterType(), CharacterType())


class StringLiteralTypeDef(TypeDef):
    def __init__(self):
        # pascal literals never have spaces, so the user can never create a type
        # named "string literal" to cause an issue with this type.
        super().__init__('string literal', StringLiteralType(), StringLiteralType())


class RealLiteralTypeDef(TypeDef):
    def __init__(self):
        super().__init__('real literal', RealType(), RealType())


class OrdinalLiteralTypeDef(TypeDef):
    def __init__(self, identifier, denoter, basetype):
        assert isinstance(basetype, OrdinalType)
        assert isinstance(denoter, OrdinalType)
        super().__init__(identifier, denoter, basetype)


class IntegerLiteralTypeDef(OrdinalLiteralTypeDef):
    def __init__(self):
        super().__init__('integer literal', IntegerType(), IntegerType())


class BooleanLiteralTypeDef(OrdinalLiteralTypeDef):
    def __init__(self):
        super().__init__('boolean literal', BooleanType(), BooleanType())


class CharacterLiteralTypeDef(OrdinalLiteralTypeDef):
    def __init__(selfself):
        super().__init__('character literal', CharacterType(), CharacterType())


class ActivationTypeDef(TypeDef):
    pass


class ProcedureTypeDef(ActivationTypeDef):
    def __init__(self):
        super().__init__('n/a', ProcedureType(), ProcedureType())


class FunctionTypeDef(ActivationTypeDef):
    def __init__(self):
        super().__init__('n/a', FunctionType(), FunctionType())
