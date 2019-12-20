class BaseType:
    def __init__(self):
        self.size = 0
        self.typename = ""

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
    pass


class IntegerType(OrdinalType):
    def __init__(self):
        super().__init__()
        self.typename = "integer"
        self.size = 4


class CharacterType(OrdinalType):
    def __init__(self):
        super().__init__()
        self.typename = "char"
        self.size = 2


class BooleanType(OrdinalType):
    def __init__(self):
        super().__init__()
        self.typename = "Boolean"
        self.size = 1


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
    pass


class ArrayType(StructuredType):
    # TODO: minindex and maxindex can be values of any OrdinalType, not just integers
    # Do we convert those values to integers during compilation?  Probably?
    def __init__(self, arrayoftype, minindex, maxindex):
        assert isinstance(arrayoftype, BaseType)
        super().__init__()
        self.typename = "array of {}".format(str(arrayoftype))
        self.minindex = minindex
        self.maxindex = maxindex
        self.size = (maxindex-minindex+1) * arrayoftype.size


class StringType(ArrayType):
    def __init__(self, maxindex):
        super().__init__(CharacterType(), 1, maxindex)
        self.typename = "string"


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
