import pascaltypes
from filelocation import FileLocation
from compiler_error import compiler_errstr


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
    def __init__(self, value, location, pascal_type):
        assert isinstance(location, FileLocation)
        assert isinstance(pascal_type, pascaltypes.BaseType)
        assert isinstance(value, str)
        self.value = value
        self.location = location
        self.pascal_type = pascal_type
        self.memory_address = None

    @property
    def memory_address(self):
        return self.__memory_address

    @memory_address.setter
    def memory_address(self, addr):
        self.__memory_address = addr

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
    def __init__(self, value, location, pascal_type):
        assert isinstance(pascal_type, pascaltypes.OrdinalType)
        super().__init__(value, location, pascal_type)


class IntegerLiteral(OrdinalLiteral):
    def __init__(self, value, location):
        super().__init__(value, location, pascaltypes.IntegerType())


class BooleanLiteral(OrdinalLiteral):
    # TODO - check why these values are strings instead of integers?
    def __init__(self, value, location):
        assert value in ('0', '1')
        super().__init__(value, location, pascaltypes.BooleanType())

    def __str__(self):  # pragma: no cover
        if self.value == '0':
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
        self.string_literals = {}
        self.numeric_literals = {}

    def add(self, lit):
        assert isinstance(lit, Literal), "Can only add Literals to LiteralTables"
        # character literals are treated like numbers, not string literals
        if isinstance(lit.pascal_type, pascaltypes.StringLiteralType):
            if lit.value not in self.string_literals.keys():
                self.string_literals[lit.value] = lit
        else:
            if lit.value not in self.numeric_literals.keys():
                self.numeric_literals[lit.value] = lit

    def fetch(self, value, pascal_type):
        assert isinstance(pascal_type, pascaltypes.BaseType)
        try:
            if isinstance(pascal_type, pascaltypes.StringLiteralType):
                ret = self.string_literals[value]
            else:
                ret = self.numeric_literals[value]
        except KeyError:  # pragma: no cover
            error_str = "Literal not found: {}.{}".format(str(value), pascal_type)
            raise SymbolException(error_str)
        return ret

    def __len__(self):
        return len(self.string_literals.keys()) + len(self.numeric_literals.keys())

    def __iter__(self):
        for key in self.string_literals.keys():
            yield self.string_literals[key]
        for key in self.numeric_literals.keys():
            yield self.numeric_literals[key]


class Symbol:
    def __init__(self, name, location, pascal_type):
        assert isinstance(pascal_type, pascaltypes.BaseType)
        assert isinstance(location, FileLocation)
        self.name = name
        self.location = location
        self.pascal_type = pascal_type
        self.memory_address = None
        self.__is_assigned_to = False
        # if a variable is used then undefined, is_assigned_to will be False but __was_assigned_to will be True
        self.__was_assigned_to = False
        # TODO - look at removing symbol.is_by_ref - why do symbols and parameters both have is_by_ref set?
        self.is_by_ref = False

    @property
    def memory_address(self):
        return self.__memory_address

    @memory_address.setter
    def memory_address(self, addr):
        self.__memory_address = addr

    @property
    def is_by_ref(self):
        return self.__is_by_ref

    @is_by_ref.setter
    def is_by_ref(self, by_ref):
        assert isinstance(by_ref, bool)
        self.__is_by_ref = by_ref

    @property
    def is_assigned_to(self):
        return self.__is_assigned_to

    @is_assigned_to.setter
    def is_assigned_to(self, assigned_to):
        assert isinstance(assigned_to, bool)
        if self.__is_assigned_to and (not assigned_to):
            self.__was_assigned_to = True
        self.__is_assigned_to = assigned_to

    @property
    def was_assigned_to(self):
        return self.__was_assigned_to

    def __str__(self):
        return self.name

    def __repr__(self):  # pragma: no cover
        return "{} ({}): {} @{}".format(self.name, self.location, str(self.pascal_type), self.memory_address)


class VariableSymbol(Symbol):
    def __init__(self, name, location, pascal_type):
        super().__init__(name, location, pascal_type)


class FunctionResultVariableSymbol(VariableSymbol):
    def __init__(self, name, location, pascal_type):
        super().__init__(name, location, pascal_type)


class ConstantSymbol(Symbol):
    def __init__(self, name, location, pascal_type, value):
        assert (isinstance(pascal_type, pascaltypes.OrdinalType)
                or isinstance(pascal_type, pascaltypes.RealType)
                or isinstance(pascal_type, pascaltypes.StringLiteralType)), type(pascal_type)
        super().__init__(name, location, pascal_type)
        self.value = value

    def __repr__(self):  # pragma: no cover
        ret = super().__repr__()
        ret += ' CONSTANT - value = {}'.format(self.value)
        return ret


class ActivationSymbol(Symbol):
    def __init__(self, name, location, pascal_type, parameter_list, result_type=None):
        assert isinstance(pascal_type, pascaltypes.BaseType)
        assert isinstance(parameter_list, ParameterList)
        # per 6.6.2 of the standard, only value return types from Functions are simple types and pointers.
        # Procedures are ActivationSymbols with no return type, so None is valid as well.
        assert (result_type is None
                or isinstance(result_type, pascaltypes.SimpleType)
                or isinstance(result_type, pascaltypes.PointerType))
        super().__init__(name, location, pascal_type)
        self.parameter_list = parameter_list
        self.result_type = result_type
        self.label = None

    @property
    def label(self):
        return self.__label

    @label.setter
    def label(self, label):
        if label is None or isinstance(label, Label):
            self.__label = label
        else:  # pragma: no cover
            raise TypeError("Invalid label")


class ProgramParameterSymbol(Symbol):
    def __init__(self, name, location, pascal_type, position):
        assert isinstance(pascal_type, pascaltypes.FileType)
        # position is where in the parameter list this parameter falls.  Used for assigning the program parameters
        # that are neither input nor output.  Input and Output get None for position.
        assert position is None or (isinstance(position, int) and position >= 1)
        super().__init__(name, location, pascal_type)
        self.position = position
        self.filename_memory_address = None


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
        self.local_transfer = False
        self.remote_transfer = False
        self.inside_structured_statement = False

    def __str__(self):
        return self.name


class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent = None

    def add(self, sym):
        assert isinstance(sym, Symbol) or isinstance(sym, Label) or isinstance(sym, pascaltypes.BaseType) or isinstance(
            sym, pascaltypes.EnumeratedTypeValue), "Can only add Symbols, Labels, and types to SymbolTables"
        if sym.name in self.symbols.keys():
            current_sym = self.fetch(sym.name)
            if isinstance(sym, ConstantSymbol) and isinstance(current_sym, ConstantSymbol):
                error_str = "Constant Redefined: {}".format(sym.name)
            else:
                error_str = "Symbol Redefined: {}".format(sym.name)
            if isinstance(sym, Symbol):
                error_str = compiler_errstr(error_str, None, sym.location)
            raise SymbolRedefinedException(error_str)
        # Unlike literals, where case matters ('abc' is different from 'aBc'), symbols in Pascal are
        # case-insensitive.  So, store them in our symbol table as lower-case.
        self.symbols[sym.name.lower()] = sym

    def fetch(self, name):
        current_table = self
        found_it = False
        return_obj = None
        while (not found_it) and (current_table is not None):
            if name.lower() in current_table.symbols.keys():
                return_obj = current_table.symbols[name.lower()]
                found_it = True
            else:
                current_table = current_table.parent
        assert found_it, "Identifier not found: '{}'".format(name)
        assert isinstance(return_obj, Symbol) or isinstance(return_obj, Label) or \
               isinstance(return_obj, pascaltypes.BaseType) or isinstance(return_obj, pascaltypes.EnumeratedTypeValue)
        return return_obj

    def fetch_original_symbol_table_and_type(self, type_identifier):
        # Original typedef:
        #
        # type
        #   x = integer;
        #   b = x;
        #   c = b;
        #
        # The original typedef for all of these is the integer definition.  However, c will be stored
        # with both a reference to b and a reference to the integer type definition.  Most of the
        # code will care only about the BaseType.  However, when inserting a new typedef into the symbol
        # table, we need to find the BaseType (using this function), and when determining whether two
        # types are the same, we need not only the identifier that points to the BaseType
        # but also the specific symbol table to determine if the identifier is the same for the two
        # types being compared.
        #
        # Logic similar to fetch(), but returns a tuple containing the original typedef itself, as well as a
        # reference to the SymbolTable that contains it.
        #

        return_symbol_table = self
        return_type = None

        # HACK - due to the way I defined literals with type name "integer literal" "real literal" etc.,
        # I can find the type by removing the " literal" from the end.
        if type_identifier[-7:] == "literal":
            type_identifier = type_identifier[:-8]

        # First, we get the type that corresponds to the t1_identifier and t2_identifier, keeping track
        # of which symbol table contains the record.
        done = False
        while not done:
            if return_symbol_table.exists(type_identifier):
                return_type = return_symbol_table.symbols[type_identifier.lower()]
                done = True
            else:
                return_symbol_table = return_symbol_table.parent
                assert return_symbol_table is not None, "Cannot find {}".format(type_identifier)

        # Now we work through any aliases.  If we have the original type, which has None as
        # the denoter, then we stop.  Else, the denoter is another type, so we need to then find
        # the symbol table in which that type's identifier was defined, and what the type corresponds to.
        outer_done = False
        inner_done = False
        while not outer_done:
            if return_type.denoter is None:
                outer_done = True
            else:
                return_type = return_type.denoter
                while not inner_done:
                    if return_symbol_table.exists(return_type.identifier):
                        return_type = return_symbol_table.symbols[return_type.identifier.lower()]
                        inner_done = True
                    else:
                        return_symbol_table = return_symbol_table.parent

        return return_symbol_table, return_type

    def exists(self, name):
        # only looks in the current symbol table
        return name.lower() in self.symbols.keys()

    def exists_anywhere(self, name):
        # looks in current symbol table and parents
        ret = False
        ptr = self
        while (not ret) and (ptr is not None):
            ret = ptr.exists(name)
            ptr = ptr.parent
        return ret

    def exists_prior_to_global_scope(self, name):
        # Looks in current symbol table and parents EXCEPT the global scope
        # Used to check for variable unassigned before usage warning.
        return_bool = False
        ptr = self
        while (not return_bool) and (ptr.parent is not None):
            return_bool = ptr.exists(name)
            ptr = ptr.parent
        return return_bool

    def __str__(self):  # pragma: no cover
        ret = ""
        for key in self.symbols.keys():
            ret += repr(self.symbols[key]) + "\n"
        return ret

    def add_simple_types(self):
        # the root of the program has the required types in it
        self.add(pascaltypes.IntegerType())
        self.add(pascaltypes.BooleanType())
        self.add(pascaltypes.RealType())
        self.add(pascaltypes.CharacterType())
        self.add(pascaltypes.TextFileType())
        # TODO - this is a hack due to the combination of TypeDef and BaseType into BaseType
        string_literal_type = pascaltypes.StringLiteralType()
        string_literal_type.identifier = "_string"
        self.add(string_literal_type)

    def are_same_type(self, type1_identifier, type2_identifier):
        # Most of the code that works with types only cares about the base type itself - how the type is laid out
        # in memory, what the identifiers are for enumerated types, etc.  However, the ISO standard is particular
        # about what types can be assigned to other types.
        #
        # Two typedefs are the same, if they can be traced back to the same type identifier.
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
        #   Coordinates2 = record
        #       x,y: real
        #       end;
        #   More_Coordinates = Coordinates2
        #
        # Coordinates is not the same type as Coordinates2, even though they share the same structure.  More_Coordinates
        # is the same type as Coordinates2 because they share the same type identifier.
        #
        # Additionally, the "same type identifier" has to take scope into account.  Consider the following:
        #
        # Program foo(output);
        # type
        #   z = integer;
        #   x = z;
        # procedure bar();
        #   type
        #       z = char;
        #       c = z;
        #   procedure nested();
        #       type
        #           z = real
        #           r = z
        #           i2 = x
        #
        # x, c, and r are both defined in terms of 'z', but they are different z's.  However, i2 and x are both
        # the same type.
        #
        # So, for the purpose of this function, we need to determine whether the types specified by the identifiers
        # passed into this function can be traced back to the same type identifier.  For this, we find not only the
        # original type identifier that defines each type, but if those are themselves identifiers and not type
        # definitions, then keep following back until we get to the identifier that is mapped to the base type.
        # If both t1 and t2 map back to the same string identifier **in the same SymbolTable** then they are the same
        # type.  In the second example above, type r and type i both map to the string identifier z, but that's not
        # a base type.  So one step further, and we find that r maps to real and x maps to integer, so they are not
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
        # with two real fields x and y.  However, you can NOT assign q1 to q2 or vice versa.

        type1_original_symbol_table, t1_original_type = self.fetch_original_symbol_table_and_type(type1_identifier)
        type2_original_symbol_table, type2_original_type = self.fetch_original_symbol_table_and_type(type2_identifier)

        # fetch_original_symbol_table_and_type returns a tuple (SymbolTable, Type)

        if type1_original_symbol_table != type2_original_symbol_table:
            return_bool = False
        else:
            if t1_original_type.identifier.lower() == type2_original_type.identifier.lower():
                if t1_original_type.identifier.lower() == "array":
                    assert isinstance(t1_original_type, pascaltypes.ArrayType)
                    assert isinstance(type2_original_type, pascaltypes.ArrayType)
                    # both t1 and t2 are arrays, need to see if they are in turn same type of array
                    if type1_original_symbol_table.are_same_type(t1_original_type.index_type.identifier,
                                                                 type2_original_type.index_type.identifier) \
                            and type1_original_symbol_table.are_same_type(
                        t1_original_type.component_type.identifier,
                        type2_original_type.component_type.identifier) \
                            and t1_original_type.is_packed == type2_original_type.is_packed:
                        return_bool = True
                    else:
                        return_bool = False

                else:
                    return_bool = True
            else:
                return_bool = False

        return return_bool

    def are_compatible(self, type1_identifier, type2_identifier, optional_type1_sym=None, optional_type2_sym=None):
        # per 6.4.5 of the ISO standard, as explained on p.10 of Cooper, two types are compatible if:
        # 1) Type1 and Type2 are the same type
        # 2) Type1 and Type2 are both Ordinal Types and one is subrange of the other, or both are subranges of the
        #    same host type
        # 3) Type1 and Type2 are sets, the base types of Type1 and Type2 are compatible, and either both
        #    Type1 and Type2 are packed or neither are packed
        # 4) Type1 and Type2 are string types with same number of components.

        # Today we support the first, second, and fourth conditions.
        # TODO Support the third condition when we support sets

        if type1_identifier == "_string literal":
            assert isinstance(optional_type1_sym, ConstantSymbol)
        if type2_identifier == "_string literal":
            assert isinstance(optional_type2_sym, ConstantSymbol)

        if type1_identifier == "_string literal" and type2_identifier == "_string literal":
            # need to do this before the are_same_type() else that will return true.
            return len(optional_type1_sym.value) == len(optional_type2_sym.value)
        elif self.are_same_type(type1_identifier, type2_identifier):
            return True
        else:
            type1_symbol_table, type1_type = self.fetch_original_symbol_table_and_type(type1_identifier)
            type2_symbol_table, type2_type = self.fetch_original_symbol_table_and_type(type2_identifier)

            if isinstance(type1_type, pascaltypes.OrdinalType) and isinstance(type2_type, pascaltypes.OrdinalType):
                # return true if:
                # type1 is a subrange of type2, type2 is a subrange of type1, or both are subranges of same host type
                if isinstance(type1_type, pascaltypes.SubrangeType):
                    if isinstance(type2_type, pascaltypes.SubrangeType):
                        if self.are_same_type(type1_type.host_type.identifier, type2_type.host_type.identifier):
                            return True
                        else:
                            return False
                    else:
                        if self.are_same_type(type1_type.host_type.identifier, type2_type.identifier):
                            return True
                        else:
                            return False
                else:
                    if isinstance(type2_type, pascaltypes.SubrangeType):
                        if self.are_same_type(type1_type.identifier, type2_type.host_type.identifier):
                            return True
                        else:
                            return False
                    else:
                        return False
            elif type1_type.is_string_type() and type2_type.is_string_type() \
                    and type1_type.num_items_in_array == type2_type.num_items_in_array:
                return True
            elif type1_type.is_string_type() and type2_identifier == "_string literal":
                return type1_type.num_items_in_array == len(optional_type2_sym.value)
            elif type1_identifier == "_string literal" and type2_type.is_string_type():
                return len(optional_type1_sym.value) == type2_type.num_items_in_array
            else:
                return False

    def are_assignment_compatible(self, type1_identifier, type2_identifier, optional_type2_value=None):
        # As explained on p10 of Cooper, 6.4.6 of the ISO Standard  states that type Type2 is "assignment-compatible"
        # with type Type1 if :
        # 1) Type1 and Type2 are the same type, but not a file type or type with file components
        # 2) Type1 is real and Type2 is integer
        # 3) Type1 and Type2 are compatible ordinal types, and the value with type Type2 falls in the range of Type1.
        #    Note the "value" piece is a run-time check, not a compile-time check.  At compile-time we can only check
        #    that some piece of Type2's range falls in the range of Type1.
        # 4) Type1 and Type2 are compatible set types, with all members of Type2 belonging to the base type of Type1.
        #    Like condition 3, at compile type we can check that at least one member of Type2 belongs in the base
        #    type of Type1, but the rest is a run-time check.
        # 5) Type1 and Type2 are compatible string types
        # TODO add condition 4 when we support sets

        type1_type = self.fetch_original_symbol_table_and_type(type1_identifier)[1]
        type2_type = self.fetch_original_symbol_table_and_type(type2_identifier)[1]

        # File Types, or types with file components are never assignment-compatible
        if isinstance(type1_type, pascaltypes.FileType) or isinstance(type2_type, pascaltypes.FileType):
            return_bool = False
        elif self.are_same_type(type1_identifier, type2_identifier):
            return_bool = True
        elif isinstance(type1_type, pascaltypes.OrdinalType) and isinstance(type2_type, pascaltypes.OrdinalType) and \
                self.are_compatible(type1_identifier, type2_identifier):
            # "are compatible" means Type1 and Type2 are both Ordinal Types and one is subrange of the other,
            # or both are subranges of the same host type.
            if isinstance(type1_type, pascaltypes.SubrangeType) and optional_type2_value is not None:
                # if Type2 is a constant and falls in the range of Type1 then rule 3 is true
                # from definition of "are compatible" we know that at this point either Type1 is a
                # subrange of Type2, or Type1 and Type2 are subranges of the same host type.
                if type1_type.is_in_range(optional_type2_value):
                    return_bool = True
                else:
                    return_bool = False
            elif isinstance(type1_type, pascaltypes.SubrangeType) and not isinstance(type2_type,
                                                                                     pascaltypes.SubrangeType):
                # if Type1 is a subrange type and Type2 is not, and Type2 is same type as Type1's host type then at
                # compile time, it's ok, but we need to check at runtime too.
                if self.are_same_type(type1_type.host_type.identifier, type2_identifier):
                    return_bool = True
                else:
                    return_bool = False
            elif isinstance(type1_type, pascaltypes.SubrangeType) and isinstance(type2_type, pascaltypes.SubrangeType):
                # if Type1 and Type2 are both subrange types and there is at least some overlap then rule 3 is true
                # from definition of "are compatible" above, we know that Type1 and Type2 are subranges of the
                # same host type.
                if type1_type.range_min_int <= type2_type.range_max_int and \
                        type1_type.range_max_int >= type2_type.range_min_int:
                    return_bool = True
                else:
                    return_bool = False
            elif not isinstance(type1_type, pascaltypes.SubrangeType) and isinstance(type2_type,
                                                                                     pascaltypes.SubrangeType):
                # if Type2 base type is a subrange and Type1 is not and Type1 is Type2's host type then rule 3 is true:
                # from definition of "are compatible" above, we know that Type2 is a subrange of Type1
                return_bool = True
            else:
                # if they are compatible ordinal types but none of the other tests above were true, then
                # they must be non-overlapping subranges or such, so are not assignment compatible.
                return_bool = False
        elif isinstance(type1_type, pascaltypes.RealType) and isinstance(type2_type, pascaltypes.IntegerType):
            return_bool = True
        elif type1_type.is_string_type() and type2_type.is_string_type() and self.are_compatible(type1_identifier,
                                                                                                 type2_identifier):
            return_bool = True
        elif type1_type.is_string_type() and isinstance(type2_type, pascaltypes.StringLiteralType):
            return_bool = (type1_type.num_items_in_array == len(optional_type2_value))
        else:
            return_bool = False

        return return_bool


class Parameter:
    def __init__(self, symbol, is_by_ref):
        assert isinstance(symbol, Symbol)
        assert isinstance(is_by_ref, bool)
        self.symbol = symbol
        self.is_by_ref = is_by_ref
        assert self.symbol.is_by_ref == self.is_by_ref

    @property
    def is_by_ref(self):
        return self.__is_by_ref

    @is_by_ref.setter
    def is_by_ref(self, by_ref):
        assert isinstance(by_ref, bool)
        self.__is_by_ref = by_ref

    def __str__(self):
        return_str = str(self.symbol)
        if self.is_by_ref:
            return_str = "VAR " + return_str
        return return_str


class ParameterList:
    def __init__(self):
        self.parameter_list = []

    def add(self, parameter):
        assert isinstance(parameter, Parameter)
        if self.fetch(parameter.symbol.name):
            error_str = compiler_errstr("Parameter Redefined: {}".format(parameter.symbol.name), None,
                                        parameter.symbol.location)
            raise SymbolException(error_str)
        else:
            self.parameter_list.append(parameter)

    def fetch(self, str_parameter_name):
        # returns None if not found
        return_parameter = None
        for param in self.parameter_list:
            if param.symbol.name == str_parameter_name:
                return_parameter = param
                break
        return return_parameter

    def __iter__(self):
        self.__position = 0
        return self

    def __next__(self):
        try:
            ret = self.parameter_list[self.__position]
            self.__position += 1
        except IndexError:
            raise StopIteration
        return ret

    def __str__(self):
        ret = ""
        if len(self.parameter_list) > 0:
            ret = "{}:{}".format(str(self.parameter_list[0]), self.parameter_list[0].symbol.pascal_type.identifier)
        for param in self.parameter_list[1:]:
            ret += ", " + "{}:{}".format(str(param), param.symbol.pascal_type.identifier)
        return ret

    def __len__(self):
        return len(self.parameter_list)

    def __getitem__(self, item):
        return self.parameter_list[item]
