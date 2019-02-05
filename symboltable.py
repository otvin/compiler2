import pascaltypes


class SymbolException(Exception):
    pass


class SymbolRedefinedException(SymbolException):
    pass


class Literal:
    # Literals are similar to symbols, but do not have names, and are always going to be
    # declared in global scope, regardless of where in the program they are found.
    def __init__(self, value, location, pascaltype):
        assert(isinstance(pascaltype, pascaltypes.BaseType))
        self.value = value
        self.location = location
        self.pascaltype = pascaltype
        self.memoryaddress = None


class LiteralTable:
    def __init__(self):
        self.literals = {}

    def add(self, lit):
        if not isinstance(lit, Literal):
            raise SymbolException("Can only add Literals to LiteralTables")
        if not lit.value in self.literals.keys():
            self.literals[lit.value] = lit

    def fetch(self, value):
        try:
            ret = self.literals[value]
        except KeyError:
            errstr = "Literal not found: {}".format(str(value))
            raise SymbolException(errstr)
        return ret


class Symbol:
    def __init__(self, name, location, pascaltype):
        assert (isinstance(pascaltype, pascaltypes.BaseType))
        self.name = name
        self.location = location
        self.pascaltype = pascaltype
        self.memoryaddress = None

    # TODO: Should be a setter?
    def setaddress(self, addr):
        self.memoryaddress = addr


class ConstantSymbol(Symbol):
    def __init__(self, name, location, pascaltype, value):
        # only valid constants are maxint, integers, characters, booleans, and reals per 6.3 of the iso standard
        # TODO: Will we support constant strings?
        assert (isinstance(pascaltype, pascaltypes.OrdinalType)
                or isinstance(pascaltype, pascaltypes.RealType))
        super().__init__(name, location, pascaltype)
        self.value = value


class ActivationSymbol(Symbol):
    def __init__(self, name, location, pascaltype, paramlist, returnpascaltype=None):
        assert isinstance(pascaltype, pascaltypes.ActivationType)
        assert isinstance(paramlist, ParameterList)
        # per 6.6.2 of the standard, only value return types from Functions are simple types and pointers.
        # Procedures are ActivationSymbols with no return type, so None is valid as well.
        assert (returnpascaltype is None or isinstance(returnpascaltype, pascaltypes.SimpleType)
                or isinstance(returnpascaltype, pascaltypes.PointerType))
        super().__init__(name, location, pascaltype)
        self.paramlist = paramlist
        self.returnpascaltype = returnpascaltype


class LabelSymbol(Symbol):
    pass


class ParameterList:
    def __init__(self):
        self.paramlist = []

    def add(self, sym):
        assert isinstance(sym, Symbol)
        self.paramlist.append(sym)


class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent = None

    def add(self, sym):
        if not isinstance(sym, Symbol):
            raise SymbolException("Can only add Symbols to SymbolTables")
        if sym.name in self.symbols.keys():
            errstr = "Symbol Redefined: {}".format(sym.name)
            raise SymbolRedefinedException(errstr)
        self.symbols[sym.name.lower()] = sym

    def fetch(self, name):
        curtable = self
        foundit = False
        ret = None
        while (not foundit) and (curtable is not None):
            if name.lower() in curtable.symbols.keys():
                ret = curtable.symbols[name.lower()]
                foundit = True
            else:
                curtable = curtable.parent
        return ret

    def exists(self, name):
        # only looks in the current symbol table
        return name.lower() in self.symbols.keys()

    def existsanywhere(self, name):
        # looks in current symbol table and parents
        ret = False
        ptr = self
        while (not ret) and (ptr is not None):
            ret = ptr.exists(name)
            ptr = ptr.parent
        return ret
