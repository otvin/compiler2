class PascalTypeException(Exception):
    pass


class BaseType:
    def __init__(self):
        self.size = 0
        self.typename = None

    def __str__(self):
        return self.typename

    def __repr__(self):
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

    def min_item(self):  # pragma: no cover
        # this is a pure virtual function
        # returns the smallest possible value of the type, as a string
        raise NotImplementedError("min_item() not implemented")

    def max_item(self):  # pragma: nocover
        # this is a pure virtual function
        # returns the largest possible value of the type, as a string
        raise NotImplementedError("max_item() not implemented")


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

    def min_item(self):
        return chr(1)

    def max_item(self):
        return chr(255)


class BooleanType(OrdinalType):
    def __init__(self):
        super().__init__()
        self.typename = "Boolean"
        self.size = 1

    def __getitem__(self, n):
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
    def __init__(self, identifier, typename, value):
        assert isinstance(identifier, str)
        assert isinstance(typename, str)
        assert isinstance(value, int)
        assert value >= 0
        self.identifier = identifier
        self.typename = typename
        self.value = value

    # allows us to use TypeDefinitions in Symbol tables, and yet keep the vocabluary in the TypeDefinition
    # such that matches the terminology in the ISO standard
    @property
    def name(self):
        return self.identifier

    def __str__(self):
        return self.identifier

    def __repr__(self):
        return "ID:{} for Type:{} with value:{}".format(self.identifier, self.typename, self.value)


class EnumeratedType(OrdinalType):
    # TODO - remove the typename - it's only used for printout.  The identifier for symbol table is on the typedef
    def __init__(self, typename, value_list):
        i = 0
        value_identifier_list = []
        while i < len(value_list):
            assert isinstance(value_list[i], EnumeratedTypeValue)
            assert value_list[i].typename == typename
            assert value_list[i].value == i
            # cannot define the same constant multiple times in the same type
            assert value_list[i].identifier not in value_identifier_list
            value_identifier_list.append(value_list[i].identifier)
            i += 1

        super().__init__()
        if len(value_list) > 255:
            errstr = "Enumerated type '{}' has {} identifiers.  Maximum is 255."
            errstr = errstr.format(typename, str(len(value_list)))
            raise PascalTypeException(errstr)
        self.typename = typename
        self.size = 1
        self.value_list = value_list

    def __str__(self):  # pragma: no cover
        return "Enumerated type: {}".format(self.typename)

    def __repr__(self):  # pragma: no cover
        ret = "Enumerated type: {} with values (".format(self.typename)
        for i in self.value_list:
            ret = ret + str(i) + ', '
        ret = ret[:-2] + ')'
        return ret

    def __getitem__(self, n):
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
        if not foundit:
            errstr = "'{}' is not a valid value for enumerated type '{}'"
            errstr = errstr.format(s, self.typename)
            raise PascalTypeException(errstr)
        return i

    def min_item(self):
        return self.value_list[0].identifier

    def max_item(self):
        return self.value_list[-1].identifier


class SubrangeType(OrdinalType):
    # TODO - remove the typename - it's only used for printout.  The identifier for symbol table is on the typedef
    def __init__(self, typename, hosttypedef, rangemin, rangemax):
        assert isinstance(hosttypedef, TypeDef)
        assert isinstance(hosttypedef.basetype, OrdinalType)
        super().__init__()
        self.typename = typename
        self.size = hosttypedef.basetype.size
        self.hosttypedef = hosttypedef
        # this is needed because Pycharm shows some inaccurate "errors" if I do not.
        assert isinstance(self.hosttypedef.basetype, OrdinalType)
        self.rangemin = rangemin  # these are always strings
        self.rangemax = rangemax
        # need to convert the rangemin / rangemax to ints so we can compare them
        self.rangemin_int = self.hosttypedef.basetype.position(self.rangemin)
        self.rangemax_int = self.hosttypedef.basetype.position(self.rangemax)
        if self.rangemin_int > self.rangemax_int:
            # required in 6.4.2.4
            errstr = "Invalid subrange - value {} is not less than or equal to value {}"
            errstr = errstr.format(self.rangemin, self.rangemax)
            raise PascalTypeException(errstr)

    def __getitem__(self, n):
        # this is needed because Pycharm shows some inaccurate "errors" if I do not.
        assert isinstance(self.hosttypedef.basetype, OrdinalType)
        assert self.rangemin_int + n <= self.rangemax_int
        return self.hosttypedef.basetype[n - self.rangemin_int]

    def position(self, s):
        assert self.isinrange(s)
        # this is needed because Pycharm shows some inaccurate "errors" if I do not.
        assert isinstance(self.hosttypedef.basetype, OrdinalType)
        host_position = self.hosttypedef.basetype.position(s)
        return host_position - self.rangemin_int

    def isinrange(self, s):
        # this is needed because Pycharm shows some inaccurate "errors" if I do not.
        assert isinstance(self.hosttypedef.basetype, OrdinalType)
        host_position = self.hosttypedef.basetype.position(s)
        return self.rangemin_int <= host_position <= self.rangemax_int

    def __str__(self):  # pragma: no cover
        return "Subrange type: '{}'".format(self.typename)

    def __repr__(self):  # pragma: no cover
        retstr = "Subrange type: '{}'.  Hosttypedef: {} \n rangemin: {}  rangemax: {}"
        retstr = retstr.format(self.typename, repr(self.hosttypedef), self.rangemin, self.rangemax)
        retstr += "\nrangemin_int: {}  rangemax_int: {}".format(str(self.rangemin_int), str(self.rangemax_int))
        return retstr

    def min_item(self):
        return self.rangemin

    def max_item(self):
        return self.rangemax


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
        #todo - make consistent with typedef - pointsto_typedef vs. pointstotype
        self.pointstotype = pointstotype


class StructuredType(BaseType):
    def __init__(self):
        super().__init__()
        self.ispacked = False  # TODO handle packed structures


class ArrayType(StructuredType):
    def __init__(self, indextypedef, componenttypedef, ispacked):
        assert isinstance(indextypedef, TypeDef)
        assert isinstance(indextypedef.basetype, OrdinalType)
        assert isinstance(componenttypedef, TypeDef)
        assert isinstance(ispacked, bool)

        super().__init__()
        self.typename = "array"
        self.indextypedef = indextypedef
        self.componenttypedef = componenttypedef
        self.ispacked = ispacked

        assert isinstance(self.indextypedef.basetype, OrdinalType)  # to prevent PyCharm from flagging violations
        self.indexmin = self.indextypedef.basetype.min_item()  # just like Subranges, these are always strings
        self.indexmax = self.indextypedef.basetype.max_item()
        # need to convert the rangemin / rangemax to ints so we can compare them
        self.indexmin_int = self.indextypedef.basetype.position(self.indexmin)
        self.indexmax_int = self.indextypedef.basetype.position(self.indexmax)
        self.numitemsinarray = (self.indexmax_int - self.indexmin_int) + 1

        self.size = self.numitemsinarray * self.componenttypedef.basetype.size

    def __repr__(self):  # pragma: no cover
        retstr = ""
        if self.ispacked:
            retstr = "Packed "
        retstr += "Array [{}] of {} (size {} bytes)".format(repr(self.indextypedef), repr(self.componenttypedef),
                                                            self.size)
        retstr += "\n basetype size: {}".format(self.componenttypedef.basetype.size)


        return retstr


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

    def get_pointer_to(self):
        # returns a new typedef that is a pointer to the current typedef
        bt = PointerType(self.basetype)
        ret = PointerTypeDef("_ptrto_"+self.identifier, bt, bt, self)
        return ret

    # allows us to use TypeDefs in Symbol tables, and yet keep the vocabluary in the TypeDef
    # such that matches the terminology in the ISO standard
    @property
    def name(self):
        return self.identifier

    def __str__(self):
        return "TypeDef '{}'".format(self.name)

    def __repr__(self):  # pragma: no cover
        if isinstance(self.basetype, SubrangeType):
            ret = "TypeDef '{}' with denoter {} and hosttype of \n\t{}\n\tminimum: {}  maximum: {}"
            ret = ret.format(self.name, str(self.denoter), str(repr(self.basetype.hosttypedef)),
                             self.basetype.rangemin, self.basetype.rangemax)
            ret += "\nrangemin_int: {}  rangemax_int: {}".format(str(self.basetype.rangemin_int), str(self.basetype.rangemax_int))

        else:
            ret = "TypeDef '{}' with denoter {} and basetype {}"
            ret = ret.format(self.name, str(self.denoter), str(repr(self.basetype)))
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
    def __init__(self):
        super().__init__('char literal', CharacterType(), CharacterType())


class ActivationTypeDef(TypeDef):
    pass


class ProcedureTypeDef(ActivationTypeDef):
    def __init__(self):
        super().__init__('n/a', ProcedureType(), ProcedureType())


class FunctionTypeDef(ActivationTypeDef):
    def __init__(self):
        super().__init__('n/a', FunctionType(), FunctionType())


class PointerTypeDef(TypeDef):
    def __init__(self, identifier, denoter, basetype, pointsto_typedef):
        assert isinstance(basetype, PointerType)
        assert isinstance(pointsto_typedef, TypeDef)
        # todo - assert that the pointsto_typedef and the basetype.pointstotype are the same
        super().__init__(identifier, denoter, basetype)
        self.pointsto_typedef = pointsto_typedef


class StructuredTypeDef(TypeDef):
    pass


class ArrayTypeDef(StructuredTypeDef):
    def __init__(self, identifier, denoter, basetype):
        assert isinstance(basetype, ArrayType)
        super().__init__(identifier, denoter, basetype)
