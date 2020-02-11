import pascaltypes
from filelocation import FileLocation


class SymbolException(Exception):
    pass


class SymbolRedefinedException(SymbolException):
    pass


class Literal:
    # Literals are similar to symbols, but do not have names, and are always going to be
    # declared in global scope, regardless of where in the program they are found.
    # The value of a literal is always a string, because most times it comes in from parsing
    # tokens, and tokens are strings.  Having a mix of strings and numbers might cause problems
    # later so we keep it a string.

    # TODO - now that Literals have "names," make Literal subclass from Symbol and instead of
    # name being the property for value, have value be the property for name.
    def __init__(self, value, location, pascaltype):
        assert isinstance(location, FileLocation)
        assert isinstance(pascaltype, pascaltypes.BaseType)
        assert isinstance(value, str)
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

    @property
    def name(self):
        return str(self.value)

    def __str__(self):
        return str(self.value)


class StringLiteral(Literal):
    def __init__(self, value, location):
        assert isinstance(value, str)
        super().__init__(value, location, pascaltypes.StringLiteralType())


class OrdinalLiteral(Literal):
    def __init__(self, value, location, pascaltype):
        assert(isinstance(pascaltype, pascaltypes.OrdinalType))
        super().__init__(value, location, pascaltype)


class IntegerLiteral(OrdinalLiteral):
    def __init__(self, value, location):
        super().__init__(value, location, pascaltypes.IntegerType())


class BooleanLiteral(OrdinalLiteral):
    def __init__(self, value, location):
        assert value in ('0', '1')
        super().__init__(value, location, pascaltypes.BooleanType())

    def __str__(self):
        if self.value == 0:
            return "FALSE"
        else:
            return "TRUE"


class CharacterLiteral(OrdinalLiteral):
    def __init__(self, value, location):
        assert isinstance(value, str)
        assert len(value) == 1
        super().__init__(value, location, pascaltypes.CharacterType())


class RealLiteral(Literal):
    def __init__(self, value, location):
        super().__init__(value, location, pascaltypes.RealType())


class LiteralTable:
    def __init__(self):
        self.stringliterals = {}
        self.numericliterals = {}

    def add(self, lit):
        if not isinstance(lit, Literal):
            raise SymbolException("Can only add Literals to LiteralTables")
        # character literals are treated like numbers, not string literals
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
        assert isinstance(pascaltype, pascaltypes.BaseType)
        assert isinstance(location, FileLocation)
        self.name = name
        self.location = location
        self.pascaltype = pascaltype
        self.memoryaddress = None
        # TODO - look at removing symbol.is_byref - why do symbols and parameters both have is_byref set?
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
        return "{} ({}): {} @{}".format(self.name, self.location, str(self.pascaltype), self.memoryaddress)


class VariableSymbol(Symbol):
    def __init__(self, name, location, pascaltype):
        super().__init__(name, location, pascaltype)


class FunctionResultVariableSymbol(VariableSymbol):
    def __init__(self, name, location, pascaltype):
        super().__init__(name, location, pascaltype)


class ConstantSymbol(Symbol):
    def __init__(self, name, location, pascaltype, value):
        assert (isinstance(pascaltype, pascaltypes.OrdinalType)
                or isinstance(pascaltype, pascaltypes.RealType)
                or isinstance(pascaltype, pascaltypes.StringLiteralType)), type(pascaltype)
        super().__init__(name, location, pascaltype)
        self.value = value

    def __repr__(self):
        ret = super().__repr__()
        ret += ' CONSTANT - value = {}'.format(self.value)
        return ret


class ActivationSymbol(Symbol):
    # TODO - rename returntype as resulttype to be consistent with 6.6.2 of the standard
    def __init__(self, name, location, pascaltype, paramlist, returntype=None):
        assert isinstance(pascaltype, pascaltypes.BaseType)
        assert isinstance(paramlist, ParameterList)
        # per 6.6.2 of the standard, only value return types from Functions are simple types and pointers.
        # Procedures are ActivationSymbols with no return type, so None is valid as well.
        assert (returntype is None
                or isinstance(returntype, pascaltypes.SimpleType)
                or isinstance(returntype, pascaltypes.PointerType))
        super().__init__(name, location, pascaltype)
        self.paramlist = paramlist
        self.returntype = returntype
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


class ProgramParameterSymbol(Symbol):
    def __init__(self, name, location, pascaltype, position):
        assert isinstance(pascaltype, pascaltypes.FileType)
        assert isinstance(position, int)
        assert position >= 1  # position = where in the program parameter list this identifier falls
        super().__init__(name, location, pascaltype)
        self.position = position


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


class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent = None

    def add(self, sym):
        assert isinstance(sym, Symbol) or isinstance(sym, Label) or \
               isinstance(sym, pascaltypes.BaseType) or isinstance(sym, pascaltypes.EnumeratedTypeValue), \
               "Can only add Symbols, Labels, and types to SymbolTables"
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
            isinstance(ret, pascaltypes.BaseType) or isinstance(ret, pascaltypes.EnumeratedTypeValue)
        return ret

    def fetch_originalsymtable_andtype(self, type_identifier):
        # Original typedef:
        #
        # type
        #   a = integer;
        #   b = a;
        #   c = b;
        #
        # The original typedef for all of these is the integer definition.  However c will be stored
        # with both a reference to b as well as a reference to the integer type definition.  Most of the
        # code will care only about the BaseType.  However, when inserting a new typedef into the symbol
        # table, we need to find the BaseType (using this function), and when determining whether two
        # types are the same, we need not only the identifier that points to the BaseType
        # but also the specific symbol table to determine if the identifier is the same for the two
        # types being compared.
        #
        # Logic similar to fetch(), but returns a tuple containing the original typedef itself, as well as a
        # reference to the symboltable that contains it.
        #

        ret_symtable = self
        ret_type = None

        # HACK - due to the way I defined literals with type name "integer literal" "real literal" etc,
        # I can find the type by removing the " literal" from the end.
        if type_identifier[-7:] == "literal":
            type_identifier = type_identifier[:-8]

        # First, we get the type that corresponds to the t1_identifier and t2_identifier, keeping track
        # of which symbol table contains the record.
        done = False
        while not done:
            if ret_symtable.exists(type_identifier):
                ret_type = ret_symtable.symbols[type_identifier.lower()]
                done = True
            else:
                ret_symtable = ret_symtable.parent
                assert ret_symtable is not None, "Cannot find {}".format(type_identifier)

        # Now we work through any aliases.  If we have the original type, which has None as
        # the denoter, then we stop.  Else, the denoter is another type, so we need to then find
        # the symbol table in which that type's idenfifier was defined, and what the type corresponds to.
        outerdone = False
        innerdone = False
        while not outerdone:
            if ret_type.denoter is None:
                outerdone = True
            else:
                ret_type = ret_type.denoter
                while not innerdone:
                    if ret_symtable.exists(ret_type.identifier):
                        ret_type = ret_symtable.symbols[ret_type.identifier.lower()]
                        innerdone = True
                    else:
                        ret_symtable = ret_symtable.parent

        return ret_symtable, ret_type

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
        self.add(pascaltypes.IntegerType())
        self.add(pascaltypes.BooleanType())
        self.add(pascaltypes.RealType())
        self.add(pascaltypes.CharacterType())
        # TODO - this is a hack due to the combination of TypeDef and BaseType into BaseType
        slt = pascaltypes.StringLiteralType()
        slt.identifier = "_string"
        self.add(slt)

    def are_same_type(self, t1_identifier, t2_identifier):
        # Most of the code that works with types only cares about the base type itself - how the type is laid out
        # in memory, what the identifiers are for enumerated types, etc.  However, the ISO standard is particular
        # about what types can be assigned to other types.
        #
        # Two type defs are the same, if they can be traced back to the same type identifier.
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
        #
        # So, for the purpose of this function, we need to determine whether the types specified by the identifiers
        # passed into this function can be traced back to the same type identifier.  For this, we find not only the
        # original type identifier that defines each type, but if those are themselves identifiers and not type
        # definitions, then keep following back until we get to the identifier that is mapped to the base type.
        # If both t1 and t2 map back to the same string identifier *in the same symboltable* then they are the same
        # type.  In the second example above, type r and type i both map to the string identifier z, but that's not
        # a base type.  So one step further and we find that r maps to real and i maps to integer, so they are not
        # the same type.
        #
        # Program foo2(output);
        # type
        #   Coordinates = record x,y:real;
        #   c1 = Coordinates;
        #   end;
        # Procedure bar2()
        #   type
        #       Coordinates = record x,y,z,a,b:real;
        #       c2 = Coordinates;
        #   Procedure nested2()
        #       type
        #           Coordinates = record x,y:real;
        #           c3 = Coordinates
        #       var
        #           q1:c1;
        #           q2:c2;
        #
        # In this example, q1 is of type c1, which is of type Coordinates, which is a record with two real
        # fields: x and y.  q2 is of type c2, which is also of a type named Coordinates, which is also a record
        # with two real fields x and y.  However, you can NOT assign q1 to q2 or vice-versa.

        t1_originalsymtable, t1_originaltype = self.fetch_originalsymtable_andtype(t1_identifier)
        t2_originalsymtable, t2_originaltype = self.fetch_originalsymtable_andtype(t2_identifier)

        # fetch_originalsymtable_andtypedef returns a tuple (symtable, typdef)

        if t1_originalsymtable != t2_originalsymtable:
            ret = False
        else:
            if t1_originaltype.identifier.lower() == t2_originaltype.identifier.lower():
                if t1_originaltype.identifier.lower() == "array":
                    assert isinstance(t1_originaltype, pascaltypes.ArrayType)
                    assert isinstance(t2_originaltype, pascaltypes.ArrayType)
                    # both t1 and t2 are arrays, need to see if they are in turn same type of array
                    if t1_originalsymtable.are_same_type(t1_originaltype.indextype.identifier,
                                                         t2_originaltype.indextype.identifier) \
                            and t1_originalsymtable.are_same_type(t1_originaltype.componenttype.identifier,
                                                                  t2_originaltype.componenttype.identifier) \
                            and t1_originaltype.ispacked == t2_originaltype.ispacked:
                        ret = True
                    else:
                        ret = False

                else:
                    ret = True
            else:
                ret = False

        return ret

    def are_compatible(self, t1_identifier, t2_identifier, optional_t1_sym=None, optional_t2_sym=None):
        # per 6.4.5 of the ISO standard, as explained on p.10 of Cooper, two types are compatible if:
        # 1) T1 and T2 are the same type
        # 2) T1 and T2 are both Ordinal Types and one is subrange of the other, or both are subranges of the
        #    same host type
        # 3) T1 and T2 are sets, the base types of T1 and T2 are compatible, and either both T1 and T2 are packed
        #    or neither are packed
        # 4) T1 and T2 are string types with same number of components.

        # Today we support the first, second, and fourth conditions.

        if t1_identifier == "_string literal":
            assert isinstance(optional_t1_sym, ConstantSymbol)
        if t2_identifier == "_string literal":
            assert isinstance(optional_t2_sym, ConstantSymbol)

        if t1_identifier == "_string literal" and t2_identifier == "_string literal":
            # need to do this before the are_same_type() else that will return true.
            return len(optional_t1_sym.value) == len(optional_t2_sym.value)
        elif self.are_same_type(t1_identifier, t2_identifier):
            return True
        else:
            t1_symtab, t1_type = self.fetch_originalsymtable_andtype(t1_identifier)
            t2_symtab, t2_type = self.fetch_originalsymtable_andtype(t2_identifier)

            if isinstance(t1_type, pascaltypes.OrdinalType) and isinstance(t2_type, pascaltypes.OrdinalType):
                # return true if:
                # t1 is a subrange of t2, t2 is a subrange of t1, or both are subranges of same host type
                if isinstance(t1_type, pascaltypes.SubrangeType):
                    if isinstance(t2_type, pascaltypes.SubrangeType):
                        if self.are_same_type(t1_type.hosttype.identifier, t2_type.hosttype.identifier):
                            return True
                        else:
                            return False
                    else:
                        if self.are_same_type(t1_type.hosttype.identifier, t2_type.identifier):
                            return True
                        else:
                            return False
                else:
                    if isinstance(t2_type, pascaltypes.SubrangeType):
                        if self.are_same_type(t1_type.identifier, t2_type.hosttype.identifier):
                            return True
                        else:
                            return False
                    else:
                        return False
            elif t1_type.is_string_type() and t2_type.is_string_type() \
                    and t1_type.numitemsinarray == t2_type.numitemsinarray:
                return True
            elif t1_type.is_string_type() and t2_identifier == "_string literal":
                return t1_type.numitemsinarray == len(optional_t2_sym.value)
            elif t1_identifier == "_string literal" and t2_type.is_string_type():
                return len(optional_t1_sym.value) == t2_type.numitemsinarray
            else:
                return False

    def are_assignment_compatible(self, t1_identifier, t2_identifier, optional_t2_value=None):
        # As explained on p10 of Cooper, 6.4.6 of the ISO Standard  states that type T2 is "assignment-compatible"
        # with type T1 if :
        # 1) T1 and T2 are the same type, but not a file type or type with file components
        # 2) T1 is real and T2 is integer
        # 3) T1 and T2 are compatible ordinal types, and the value with type T2 falls in the range of T1.  Note
        #    the "value" piece is a run-time check, not a compile-time check.  At compile-time we can only check
        #    that some piece of T2's range falls in the range of T1.
        # 4) T1 and T2 are compatible set types, with all members of T2 belonging to the base type of T1.  Again
        #    like condition 3, at compile type we can check that at least one member of T2 belongs in the base
        #    type of T1, but the rest is a run-time check.
        # 5) T1 and T2 are compatible string types
        #

        t1type = self.fetch_originalsymtable_andtype(t1_identifier)[1]
        t2type = self.fetch_originalsymtable_andtype(t2_identifier)[1]

        # File Types, or types with file components are never assignment-compatible
        if isinstance(t1type, pascaltypes.FileType) or isinstance(t2type, pascaltypes.FileType):
            ret = False
        elif self.are_same_type(t1_identifier, t2_identifier):
            ret = True
        elif isinstance(t1type, pascaltypes.OrdinalType) and isinstance(t2type, pascaltypes.OrdinalType) and \
                self.are_compatible(t1_identifier, t2_identifier):
            # "are compatible" means T1 and T2 are both Ordinal Types and one is subrange of the other,
            # or both are subranges of the same host type.
            if isinstance(t1type, pascaltypes.SubrangeType) and optional_t2_value is not None:
                # if t2 is a constant and falls in the range of t1 then rule 3 is true
                # from definition of "are compatible" we know that at this point either t1 is a
                # subrange of t2, or t1 and t2 are subranges of the same host type.
                if t1type.isinrange(optional_t2_value):
                    ret = True
                else:
                    ret = False
            elif isinstance(t1type, pascaltypes.SubrangeType) and not isinstance(t2type, pascaltypes.SubrangeType):
                # if t1 is a subrange type and t2 is not, and t2 is same type as t1's host type then at
                # compile time, it's ok, but we need to check at runtime too.
                if self.are_same_type(t1type.hosttype.identifier, t2_identifier):
                    ret = True
                else:
                    ret = False
            elif isinstance(t1type, pascaltypes.SubrangeType) and isinstance(t2type, pascaltypes.SubrangeType):
                # if t1 and t2 are both subrange types and there is at least some overlap then rule 3 is true
                # from definition of "are compatible" above, we know that t1 and t2 are subranges of the
                # same host type.
                if t1type.rangemin_int <= t2type.rangemax_int and t1type.rangemax_int >= t2type.rangemin_int:
                    ret = True
                else:
                    ret = False
            elif not isinstance(t1type, pascaltypes.SubrangeType) and isinstance(t2type, pascaltypes.SubrangeType):
                # if t2 base type is a subrange and t1 is not and t1 is t2's host type then rule 3 is true:
                # from definition of "are compatible" above, we know that t2 is a subtange of t1
                ret = True
            else:
                # if they are compatible ordinal types but none of the other tests above were true, then
                # they must be non-overlapping subranges or such, so are not assignment compatible.
                ret = False
        elif isinstance(t1type, pascaltypes.RealType) and isinstance(t2type, pascaltypes.IntegerType):
            ret = True
        elif t1type.is_string_type() and t2type.is_string_type() and self.are_compatible(t1_identifier, t2_identifier):
            ret = True
        elif t1type.is_string_type() and isinstance(t2type, pascaltypes.StringLiteralType):
            ret = (t1type.numitemsinarray == len(optional_t2_value))
        else:
            ret = False

        return ret


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
            ret = "{}:{}".format(str(self.paramlist[0]), self.paramlist[0].symbol.pascaltype.identifier)
        for param in self.paramlist[1:]:
            ret += ", " + "{}:{}".format(str(param), param.symbol.pascaltype.identifier)
        return ret

    def __len__(self):
        return len(self.paramlist)

    def __getitem__(self, item):
        return self.paramlist[item]
