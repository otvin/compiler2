import pascaltypes
from filelocation import FileLocation


class SymbolException(Exception):
    pass


class SymbolRedefinedException(SymbolException):
    pass


class Literal:
    # Literals are similar to symbols, but do not have names, and are always going to be
    # declared in global scope, regardless of where in the program they are found.
    def __init__(self, value, location, pascaltype):
        assert isinstance(location, FileLocation)
        assert isinstance(pascaltype, pascaltypes.BaseType)
        self.value = value
        self.location = location
        self.pascaltype = pascaltype
        self.memoryaddress = None

    @property
    def memoryaddress(self):
        return self.__memoryaddress

    @memoryaddress.setter
    def memoryaddress(self, addr):
        self.__memoryaddress = addr

    def __str__(self):
        return str(self.value)


class StringLiteral(Literal):
    def __init__(self, value, location):
        assert isinstance(value, str)
        super().__init__(value, location, pascaltypes.StringLiteralType())


class NumericLiteral(Literal):
    def __init__(self, value, location, pascaltype):
        assert (isinstance(pascaltype, pascaltypes.RealType) or isinstance(pascaltype, pascaltypes.IntegerType))
        super().__init__(value, location, pascaltype)
        self.pascaltype = pascaltype


class BooleanLiteral(Literal):
    def __init__(self, value, location):
        assert value == 0 or value == 1
        super().__init__(value, location, pascaltypes.BooleanType())

    def __str__(self):
        if self.value == 0:
            return "FALSE"
        else:
            return "TRUE"


class LiteralTable:
    def __init__(self):
        self.stringliterals = {}
        self.numericliterals = {}

    def add(self, lit):
        if not isinstance(lit, Literal):
            raise SymbolException("Can only add Literals to LiteralTables")
        if isinstance(lit.pascaltype, pascaltypes.StringLiteralType):
            if lit.value not in self.stringliterals.keys():
                self.stringliterals[lit.value] = lit
        else:
            if lit.value not in self.numericliterals.keys():
                self.numericliterals[lit.value] = lit

    def fetch(self, value, pascaltype):
        assert isinstance(pascaltype, pascaltypes.BaseType)
        try:
            if isinstance(pascaltype, pascaltypes.StringLiteralType):
                ret = self.stringliterals[value]
            else:
                ret = self.numericliterals[value]
        except KeyError:
            errstr = "Literal not found: {}.{}".format(str(value), pascaltype)
            raise SymbolException(errstr)
        return ret

    def __len__(self):
        return len(self.stringliterals.keys()) + len(self.numericliterals.keys())

    def __iter__(self):
        for key in self.stringliterals.keys():
            yield self.stringliterals[key]
        for key in self.numericliterals.keys():
            yield self.numericliterals[key]


class Symbol:
    def __init__(self, name, location, pascaltype):
        assert (isinstance(pascaltype, pascaltypes.BaseType))
        self.name = name
        self.location = location
        self.pascaltype = pascaltype
        self.memoryaddress = None
        self.is_byref = False

    @property
    def memoryaddress(self):
        return self.__memoryaddress

    @memoryaddress.setter
    def memoryaddress(self, addr):
        self.__memoryaddress = addr

    @property
    def is_byref(self):
        return self.__is_byref

    @is_byref.setter
    def is_byref(self, byref):
        assert isinstance(byref, bool)
        self.__is_byref = byref

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{} ({}): {} @{}".format(self.name, self.location, self.pascaltype.typename, self.memoryaddress)


class VariableSymbol(Symbol):
    def __init__(self, name, location, pascaltype):
        super().__init__(name, location, pascaltype)


class FunctionResultVariableSymbol(VariableSymbol):
    def __init__(self, name, location, pascaltype):
        super().__init__(name, location, pascaltype)


class ConstantSymbol(Symbol):
    def __init__(self, name, location, pascaltype, value):
        # only valid constants are maxint, integers, character strings, booleans, and reals per 6.3 of the iso standard
        assert (isinstance(pascaltype, pascaltypes.OrdinalType)
                or isinstance(pascaltype, pascaltypes.RealType)
                or isinstance(pascaltype, pascaltypes.StringLiteralType))
        super().__init__(name, location, pascaltype)
        self.value = value

    def __repr__(self):
        ret = super().__repr__()
        ret += ' CONSTANT - value = {}'.format(self.value)
        return ret


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
        self.label = None

    @property
    def label(self):
        return self.__label

    @label.setter
    def label(self, lab):
        if lab is None or isinstance(lab, Label):
            self.__label = lab
        else:  # pragma: no cover
            raise TypeError("Invalid label")


class Label:
    # TODO - is a label a standalone thing or is a label something that modifies another statement?

    """ Labels are declared, like variables.  If a label never has a goto transfer control to it, then that is a
        compiler warning.  Similarly, the label statement cannot appear inside structured statements like 'for,'
        'repeat,' or 'while.'

        Pascal allows
        inter-procedural gotos, also called non-local gotos.  These are strictly limited to jumping back to an
        enclosing block of the goto.  Inter-procedural gotos are only used in nested procedures in Pascal.  For
        example, see the code below:

        Program test(output);

        Procedure Outer();
        Label 123;
            Procedure Inner();
            begin
                writeln('got here!');
                goto 123;
                writeln('will never get here!');
            end; {procedure inner}
        begin
            writeln('starting flow');
            Inner();
            writeln('will never get here either!');
            123:
            writeln('control transferred here');
        end; {procedure outer}
        begin {main}
            Outer();
        end.

        The output will be:

        starting flow
        got here!
        control transferred here

        Please reference the 3 conditions for a goto in section 6.8.1 of the ISO Standard.

        A label that is only referenced by a goto in the same statement-sequence as the label
        will only need to be compiled to an assembly language label and the goto itself will be
        compiled to an unconditional jump.  If a goto inside a nested procedure or function transfers
        control to a label, then the label statement will need to store the machine state, and the effect
        of the goto will be to restore that saved state.
    """
    def __init__(self, name):
        self.name = name
        self.localtransfer = False
        self.remotetransfer = False
        self.insidestructuredstatement = False

    def __str__(self):
        return self.name


# The information on the enumerated types will be stored in the type table, but
class EnumeratedTypeName:
    def __init__(self, typename):
        self.typename = typename


class EnumeratedTypeValue:
    def __init__(self, value, enumeratedtypename):
        assert isinstance(enumeratedtypename, EnumeratedTypeName)
        self.value = value


class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent = None

    def add(self, sym):
        assert isinstance(sym, Symbol) or isinstance(sym, Label) or \
               isinstance(sym, pascaltypes.TypeDefinition) or isinstance(sym, pascaltypes.EnumeratedTypeValue), \
               "Can only add Symbols, Labels, and type definitions to SymbolTables"
        if sym.name in self.symbols.keys():
            current_sym = self.fetch(sym.name)
            if isinstance(sym, ConstantSymbol) and isinstance(current_sym, ConstantSymbol):
                errstr = "Constant Redefined: {}".format(sym.name)
            else:
                errstr = "Symbol Redefined: {}".format(sym.name)
            if isinstance(sym, Symbol):
                errstr += " in {}".format(sym.location)
            raise SymbolRedefinedException(errstr)
        # Unlike literals, where case matters ('abc' is different from 'aBc'), symbols in Pascal are
        # case-insensitive.  So, store them in our symbol table as lower-case.
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
        if not foundit:
            raise SymbolException("Identifier not found: '{}'".format(name))
        assert isinstance(ret, Symbol) or isinstance(ret, Label) or \
            isinstance(ret, pascaltypes.TypeDefinition) or isinstance(ret, pascaltypes.EnumeratedTypeValue)
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

    def __str__(self):
        ret = ""
        for key in self.symbols.keys():
            ret += repr(self.symbols[key]) + "\n"
        return ret

    def addsimpletypes(self):
        # the root of the program has the required types in it
        self.add(pascaltypes.TypeDefinition("integer", pascaltypes.IntegerType()))
        self.add(pascaltypes.TypeDefinition("boolean", pascaltypes.BooleanType()))
        self.add(pascaltypes.TypeDefinition("real", pascaltypes.RealType()))
        self.add(pascaltypes.TypeDefinition("char", pascaltypes.CharacterType()))

    def are_same_type(self, t1_identifier, t2_identifier):
        # Two type definitions are the same, if they can be traced back to the same type identifier.
        # Per 6.4.7 of the ISO standard, 'integer,' 'count,' and 'range' in this example are the same type:
        #
        # type
        #   count = integer;
        #   range = integer;
        #
        # However, as clarified in Cooper on p.11, if two types share the same structure, but different type identifiers
        # then they are different types.  So in this example:
        #
        # type
        #   Coordinates = record
        #       x,y: real
        #       end;
        #   Coords = record
        #       x,y: real
        #       end;
        #   MoreCoords = Coords
        #
        # Coordinates is not the same type as Coords, even though they share the same structure.  MoreCoords is the
        # same type as MoreCoords because they share the same type identifier.
        #
        # Additionally, the "same type identifier" has to take scope into account.  Consider the following:
        #
        # Program foo(output);
        # type
        #   z = integer;
        #   i = z;
        # procedure bar();
        #   type
        #       z = char;
        #       c = z;
        #   procedure nested();
        #       type
        #           z = real
        #           r = z
        #           i2 = i
        #
        # i, c, and r are both defined in terms of 'z', but they are different z's.  However i2 and i are both
        # the same type.
        pass

    def are_compatiable(self, t1_identifier, t2_identifier):
        pass

    def are_assignment_compatible(self, t1_identifier, t2_identifier):
        # As explained on p10 of Cooper, 6.4.6 of the ISO Standard  states that type T2 is "assignment-compatible"
        # with type T1 if :
        # 1) T1 and T2 are the same type, but not a file type or type with file components
        # 2) T1 is real and T2 is integer
        # 3) T1 and T2 are compatible ordinal types, and
        pass


class Parameter:
    def __init__(self, symbol, is_byref):
        assert isinstance(symbol, Symbol)
        assert isinstance(is_byref, bool)
        self.symbol = symbol
        self.is_byref = is_byref
        assert self.symbol.is_byref == self.is_byref

    @property
    def is_byref(self):
        return self.__is_byref

    @is_byref.setter
    def is_byref(self, byref):
        assert isinstance(byref, bool)
        self.__is_byref = byref

    def __str__(self):
        ret = str(self.symbol)
        if self.is_byref:
            ret = "VAR " + ret
        return ret


class ParameterList:
    def __init__(self):
        self.paramlist = []

    def add(self, param):
        assert isinstance(param, Parameter)
        if self.fetch(param.symbol.name):
            errstr = "Parameter Redefined: {} in {}".format(param.symbol.name, param.symbol.location)
            raise SymbolException(errstr)
        else:
            self.paramlist.append(param)

    def fetch(self, str_paramname):
        # returns None if not found
        ret = None
        for param in self.paramlist:
            if param.symbol.name == str_paramname:
                ret = param
                break
        return ret

    def __iter__(self):
        self.__pos = 0
        return self

    def __next__(self):
        try:
            ret = self.paramlist[self.__pos]
            self.__pos += 1
        except IndexError:
            raise StopIteration
        return ret

    def __str__(self):
        ret = ""
        if len(self.paramlist) > 0:
            ret = "{}:{}".format(str(self.paramlist[0]), self.paramlist[0].symbol.pascaltype.typename)
        for param in self.paramlist[1:]:
            ret += ", " + "{}:{}".format(str(param), param.symbol.pascaltype.typename)
        return ret

    def __len__(self):
        return len(self.paramlist)

    def __getitem__(self, item):
        return self.paramlist[item]
