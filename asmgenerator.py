import os
from tac_ir import TACBlock, TACLabelNode, TACParamNode, TACCallSystemFunctionNode, TACUnaryLiteralNode, \
    TACOperator, TACGenerator, TACCommentNode, TACBinaryNode, TACUnaryNode, TACGotoNode, TACIFZNode, \
    TACFunctionReturnNode, TACCallFunctionNode, TACBinaryNodeWithBoundsCheck
from symboltable import StringLiteral, IntegerLiteral, Symbol, Parameter, ActivationSymbol, RealLiteral, \
    FunctionResultVariableSymbol, CharacterLiteral, ConstantSymbol, ProgramParameterSymbol
from compiler_error import compiler_error_str, compiler_fail_str
from editor_settings import NUM_SPACES_IN_TAB, NUM_TABS_FOR_COMMENT
import pascaltypes


class ASMGeneratorError(Exception):
    pass


VALID_REGISTER_LIST = ["RAX", "RBX", "RCX", "RDX", "RSI", "RDI", "RBP", "RSP", "R8", "R9", "R10", "R11", "R12",
                       "R13", "R14", "R15", "R16"]

VALID_DWORD_REGISTER_LIST = ["EAX", "EBX", "ECX", "EDX", "ESI", "EDI", "EBP", "ESP", "R8D", "R9D", "R10D", "R11D",
                             "R12D", "R13D", "R14D", "R15D", "R16D"]

VALID_SCRATCH_REGISTER_LIST = ["R11", "R10", "R15", "R16"]  # TODO - Validate this list with the ABI

FILE_STATE_NOT_INITIALIZED = 0
FILE_STATE_GENERATION = 1
FILE_STATE_INSPECTION = 2


class PascalRuntimeError:
    def __init__(self, error_string, label, is_used=False):
        # we will only write the error information to the .asm file if it is invoked someplace
        assert isinstance(error_string, str)
        assert isinstance(label, str)
        self.is_used = is_used
        self.error_string = error_string
        self.label = label


def get_register_slice_by_bytes(register, num_bytes):
    assert num_bytes in [1, 2, 4, 8]
    assert register in VALID_REGISTER_LIST

    # TODO - https://stackoverflow.com/questions/41573502/why-doesnt-gcc-use-partial-registers - when we get to types
    # that are 1 or 2 bytes, need to make sure we don't get in trouble.

    if num_bytes == 8:
        return_register = register
    else:
        if register in ["RAX", "RBX", "RCX", "RDX"]:
            if num_bytes == 4:
                return_register = "E" + register[-2:]
            elif num_bytes == 2:
                return_register = register[-2:]
            else:
                return_register = register[1] + "L"
        elif register in ["RSI", "RDI", "RBP", "RSP"]:
            if num_bytes == 4:
                return_register = "E" + register[-2:]
            elif num_bytes == 2:
                return_register = register[-2:]
            else:
                return_register = register[-2:] + "L"
        else:
            if num_bytes == 4:
                return_register = register + "D"
            elif num_bytes == 2:
                return_register = register + "W"
            else:
                return_register = register + "B"
    return return_register


def integer_parameter_position_to_register(pos):
    # First six integer parameters to functions are stored in registers.
    # This function converts the position in the function parameter list to a register
    # once we get > 6 parameters it will be stack pointer offsets
    assert pos in [1, 2, 3, 4, 5, 6]

    if pos == 1:
        ret = "RDI"
    elif pos == 2:
        ret = "RSI"
    elif pos == 3:
        ret = "RDX"
    elif pos == 4:
        ret = "RCX"
    elif pos == 5:
        ret = "R8"
    else:
        ret = "R9"

    return ret


def is_integer_or_boolean_subrange_type(base_type):
    assert isinstance(base_type, pascaltypes.BaseType)
    return_bool = False
    if isinstance(base_type, pascaltypes.SubrangeType):
        if isinstance(base_type.host_type, pascaltypes.IntegerType):
            return_bool = True
        elif isinstance(base_type.host_type, pascaltypes.BooleanType):
            return_bool = True
    return return_bool


class AssemblyGenerator:
    def __init__(self, assembly_file_name, tac_generator):
        assert isinstance(tac_generator, TACGenerator)
        self.assembly_file_name = assembly_file_name
        self.assembly_file = open(assembly_file_name, 'w')
        self.tac_generator = tac_generator
        self.maximum_label_number = 0
        self.runtime_errors = []
        self.init_runtime_errors()
        self.used_x87_code = False
        self.used_calloc = False
        self.used_dispose = False

    def init_runtime_errors(self):

        # Overflow error is referenced in compiler2_system_io.asm and compiler2_stringcompare.asm
        self.runtime_errors.append(PascalRuntimeError("Overflow error", "_PASCAL_OVERFLOW_ERROR", True))
        self.runtime_errors.append(
            PascalRuntimeError("Error D.44 or D.45: Division by zero error", "_PASCAL_DIVIDE_BY_ZERO_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error D.46: Divisor in Mod must be positive", "_PASCAL_MOD_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error D.34: Cannot take sqrt() of negative number", "_PASCAL_SQRT_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error D.33: Cannot take ln() of number less than or equal to zero",
                               "_PASCAL_LN_ERROR"))
        self.runtime_errors.append(PascalRuntimeError("Error D.37: value to chr() exceeds 0-255 range for Char type",
                                                      "_PASCAL_CHR_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error D.38 or D.39: succ() or pred() exceeds range for enumerated type",
                               "_PASCAL_SUCC_PRED_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error: value exceeds range for subrange type", "_PASCAL_SUBRANGE_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error: array index out of range.", "_PASCAL_ARRAY_INDEX_RANGE_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error: dynamic memory allocation failed.", "_PASCAL_CALLOC_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error: unable to de-allocate dynamic memory.", "_PASCAL_DISPOSE_ERROR"))
        # D.14 is referenced in compiler2_system_io.asm
        self.runtime_errors.append(
            PascalRuntimeError("Error D.14: file not in inspection mode prior to get() or read().",
                               "_PASCAL_FILE_WRONG_MODE_GET_OR_READ_ERROR", True))
        # D.16 is referenced in compiler2_system_io.asm
        self.runtime_errors.append(PascalRuntimeError("Error D.16: EOF encountered during get() or read().",
                                                      "_PASCAL_FILE_GET_READ_EOF_ERROR", True))
        self.runtime_errors.append(PascalRuntimeError(
            "Error D.9: File not in generation mode prior to put(), write(), writeln(), or page().",
            "_PASCAL_FILE_NOT_GENERATION_MODE_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error D.14: File not in inspection mode prior to get() or read().",
                               "_PASCAL_FILE_NOT_INSPECTION_MODE_ERROR"))
        self.runtime_errors.append(PascalRuntimeError("Error D.10 or D.15: File undefined prior to access.",
                                                      "_PASCAL_FILE_UNDEFINED_ERROR"))
        self.runtime_errors.append(PascalRuntimeError("Error: insufficient number of command-line arguments.",
                                                      "_PASCAL_INSUFFICIENT_ARGC_ERROR"))
        self.runtime_errors.append(PascalRuntimeError("Error opening file.", "_PASCAL_FILE_OPEN_ERROR"))
        self.runtime_errors.append(
            PascalRuntimeError("Error D.48: Activation of function is undefined upon function completion.",
                               "_PASCAL_NO_RETURN_VALUE_ERROR"))

    def emit(self, s):
        self.assembly_file.write(s)

    def emit_line(self, s):
        self.emit(s + '\n')

    def emit_code(self, s, comment=None):
        if comment is None:
            self.emit_line('\t' + s)
        else:
            num_tabs = NUM_TABS_FOR_COMMENT - 1 - (len(s) // NUM_SPACES_IN_TAB)
            if num_tabs < 0:  # pragma: no cover
                num_tabs = 0
            tab_str = "\t" * num_tabs
            self.emit_line('\t' + s + tab_str + ';' + comment)

    def emit_label(self, label_name, comment=None):
        if comment is None:
            self.emit_line(label_name + ":")
        else:
            num_tabs = NUM_TABS_FOR_COMMENT - (len(label_name) // NUM_SPACES_IN_TAB)
            if num_tabs < 0:  # pragma: no cover
                num_tabs = 0
            tab_str = "\t" * num_tabs
            self.emit_line(label_name + ':' + tab_str + ';' + comment)

    def emit_section(self, section_name):
        self.emit_line("section .{}".format(section_name))

    def emit_comment(self, comment_str, indented=False):
        tab_str = ""
        if indented:
            tab_str = "\t" * NUM_TABS_FOR_COMMENT
        self.emit_line("{}; {}".format(tab_str, comment_str))

    def emit_push_xmm_register(self, reg):
        self.emit_code("SUB RSP, 16", "PUSH " + reg)
        self.emit_code("MOVDQU [RSP], " + reg)

    def emit_pop_xmm_register(self, reg):
        self.emit_code("MOVDQU " + reg + ", [RSP]", "POP " + reg)
        self.emit_code("ADD RSP, 16")

    def emit_move_to_register_from_stack(self, destination_register, symbol, comment=None):
        assert isinstance(symbol, Symbol)

        # function exists because it was written before we fixed literals.  The only difference is the assertion that
        # we are moving a symbol not a literal, and this is done so that if literals pop up someplace unexpected
        # we get a notice
        self.emit_move_to_register_from_stack_or_literal(destination_register, symbol, comment)

    def emit_move_to_register_from_stack_or_literal(self, destination_register, symbol, comment=None):
        # TODO - instead of hardcoded r10, have some way to get an available scratch register
        assert isinstance(symbol, Symbol) or isinstance(symbol, IntegerLiteral)

        if destination_register.upper() in VALID_DWORD_REGISTER_LIST and symbol.pascal_type.size == 1:
            # we can find ourselves doing pointer math where we need to multiply the value from an enumerated
            # type by an integer representing the component size of an array.  Need to zero-extend that.  It
            # may come up in other cases as well.
            move_instruction = "movzx"
            byte_keyword = " byte "
        else:
            move_instruction = "mov"
            byte_keyword = ""

        if isinstance(symbol, IntegerLiteral):
            self.emit_code("mov {}, {}".format(destination_register, symbol.value), comment)
        else:
            if symbol.is_by_ref:
                self.emit_code("mov r10, [{}]".format(symbol.memory_address), comment)
                self.emit_code("{} {}, {} [r10]".format(move_instruction, destination_register, byte_keyword))
            else:
                self.emit_code("{} {}, {} [{}]".format(move_instruction, destination_register, byte_keyword,
                                                       symbol.memory_address), comment)

    def emit_move_to_xmm_register_from_stack(self, destination_register, symbol, comment=None):
        assert isinstance(symbol, Symbol), type(symbol)
        if symbol.is_by_ref:
            self.emit_code("mov r10, [{}]".format(symbol.memory_address), comment)
            self.emit_code("movsd {}, [r10]".format(destination_register))
        else:
            self.emit_code("movsd {}, [{}]".format(destination_register, symbol.memory_address), comment)

    def emit_move_address_to_register_from_stack(self, destination_register, symbol, comment=None):
        assert isinstance(symbol, Symbol)
        if symbol.is_by_ref or isinstance(symbol.pascal_type, pascaltypes.ArrayType):
            self.emit_code("mov {}, [{}]".format(destination_register, symbol.memory_address), comment)
        else:
            # never been tested
            self.emit_code("lea {}, [{}]".format(destination_register, symbol.memory_address), comment)

    def emit_move_dereference_to_register_from_stack(self, destination_register, symbol, comment=None):
        assert isinstance(symbol, Symbol)
        assert not symbol.is_by_ref  # not 100% positive this will be true
        self.emit_code("mov r10, [{}]".format(symbol.memory_address), comment)
        self.emit_code("mov {}, [r10]".format(destination_register))

    def emit_move_to_stack_from_register(self, symbol, source_register, comment=None):
        assert isinstance(symbol, Symbol)
        if symbol.is_by_ref:
            self.emit_code("mov r10, [{}]".format(symbol.memory_address), comment)
            self.emit_code("mov [r10], {}".format(source_register))
        else:
            self.emit_code("mov [{}], {}".format(symbol.memory_address, source_register), comment)

    def emit_move_to_stack_from_xmm_register(self, symbol, source_register, comment=None):
        assert isinstance(symbol, Symbol)
        assert not symbol.is_by_ref  # if it's by ref, it will not be passed in a xmm register
        self.emit_code("movsd [{}], {}".format(symbol.memory_address, source_register), comment)

    def emit_jump_to_error(self, jump_mnemonic, error_label):
        # If there were thousands of errors, this would be slow, but there aren't
        assert isinstance(jump_mnemonic, str)
        assert jump_mnemonic[0].lower() == 'j'  # all jump instructions begin with j
        assert isinstance(error_label, str)

        found_it = False
        for runtime_error in self.runtime_errors:
            if runtime_error.label == error_label:
                runtime_error.is_used = True
                found_it = True
                break
        assert found_it  # if it's not a valid error code we have a typo
        self.emit_code("{} {}".format(jump_mnemonic, error_label))

    def emit_copy_memory(self, destination_symbol, source_symbol, num_bytes, comment="", preserve_registers=False):
        # the memory copy uses rdi, rsi, and rcx.  If preserve_regs is true, we will push/pop them to ensure
        # they are in same state as they were on entry

        # this is a bit hacky - sometimes I have a destination symbol, sometimes a register.  Since Python is
        # not statically typed, I can have one function handle either type of input, but it may not be very clean.

        assert isinstance(source_symbol, Symbol)
        assert isinstance(destination_symbol, Symbol) or (
                isinstance(destination_symbol, str) and destination_symbol.upper() in VALID_REGISTER_LIST)
        assert num_bytes > 0
        assert isinstance(source_symbol.pascal_type, pascaltypes.PointerType) or \
               isinstance(source_symbol.pascal_type, pascaltypes.ArrayType) or \
               isinstance(source_symbol.pascal_type, pascaltypes.StringLiteralType)

        if isinstance(destination_symbol, Symbol):
            assert isinstance(destination_symbol.pascal_type, pascaltypes.PointerType) or \
                   isinstance(destination_symbol.pascal_type, pascaltypes.ArrayType)

        if preserve_registers:
            self.emit_code("push rcx", "preserve registers used in memory copy")
            self.emit_code("push rsi")
            self.emit_code("push rdi")

        if isinstance(destination_symbol, Symbol):
            self.emit_code("mov rdi, [{}]".format(destination_symbol.memory_address, comment))
        else:
            self.emit_code("mov rdi, {}".format(destination_symbol))
        self.emit_code("mov rsi, [{}]".format(source_symbol.memory_address))
        self.emit_code("mov rcx, {}".format(num_bytes))
        self.emit_code("cld")
        self.emit_code("rep movsb")

        if preserve_registers:
            self.emit_code("pop rdi")
            self.emit_code("pop rsi")
            self.emit_code("pop rcx")

    def get_next_label(self):
        return_label = "_L" + str(self.maximum_label_number)
        self.maximum_label_number += 1
        return return_label

    def generate_extern_references(self):
        self.emit_code("extern fprintf")
        self.emit_code("extern fopen")
        self.emit_code("extern freopen")
        self.emit_code("extern fputc")
        self.emit_code("extern calloc")
        self.emit_code("extern free")
        self.emit_code("extern fflush")
        self.emit_code("extern stdout")

        self.emit_code("extern _PASCAL_PRINT_STRING_TYPE", "from compiler2_system_io.asm")
        self.emit_code("extern _PASCAL_GETC", "from compiler2_system_io.asm")
        self.emit_code("extern _PASCAL_STRING_COMPARE", "from compiler2_stringcompare.asm")

        self.emit_code("global _PASCAL_OVERFLOW_ERROR", "needed by compiler2_*.asm")
        self.emit_code("global _PASCAL_FILE_WRONG_MODE_GET_OR_READ_ERROR")
        self.emit_code("global _PASCAL_FILE_GET_READ_EOF_ERROR")

    def generate_data_section(self):
        self.emit_section("data")
        self.emit_comment("error handling strings")
        for runtime_error in self.runtime_errors:
            # TODO - we could iterate over all the TACBlocks, identify which errors we will need, then change
            # emit_jump_to_error to test whether or not we're invoking an error that we have marked as used.  That
            # would reduce the binary size.
            self.emit_code('_pascal_error_{} db `{}`, 0'.format(str(self.runtime_errors.index(runtime_error)),
                                                                runtime_error.error_string))
        self.emit_comment("support for write() commands")
        self.emit_code('_printf_integer_format db "%d",0')
        # TODO - this is not pascal-compliant, as should be fixed characters right-justified
        # but is better than the C default of 6 digits to the right of the decimal.
        self.emit_code('_printf_real_format db "%.12f",0')
        self.emit_code('_printf_line_feed db 10,0')
        self.emit_code('_printf_true db "TRUE",0')
        self.emit_code('_printf_false db "FALSE",0')

        self.emit_code('_filemode_write db "w",0')
        self.emit_code('_filemode_write_binary db "wb",0')
        self.emit_code('_filemode_read db "r",0')
        self.emit_code('_filemode_readbinary db "rb",0')

        if len(self.tac_generator.global_literal_table) > 0:
            next_id = 0
            for literal in self.tac_generator.global_literal_table:
                if isinstance(literal, IntegerLiteral) or isinstance(literal, CharacterLiteral):
                    # these can be defined as part of the instruction where they are loaded
                    pass
                elif isinstance(literal, StringLiteral):
                    literal_name = 'string_literal_{}'.format(next_id)
                    next_id += 1
                    if len(literal.value) > 255:
                        error_str = compiler_error_str(
                            "String literal '{}' exceeds 255 char max length.".format(literal.value), None,
                            literal.location)
                        raise ASMGeneratorError(error_str)
                    self.emit_code("{} db `{}`, 0".format(literal_name, literal.value.replace('`', '\\`')))
                    literal.memory_address = literal_name
                elif isinstance(literal, RealLiteral):
                    literal_name = 'real_literal_{}'.format(next_id)
                    next_id += 1
                    self.emit_code("{} dq {}".format(literal_name, literal.value))
                    literal.memory_address = literal_name
                else:  # pragma: no cover
                    raise ASMGeneratorError("Invalid literal type")

    def generate_subrange_test_code(self, reg, subrange_base_type):
        assert isinstance(subrange_base_type, pascaltypes.SubrangeType)
        if subrange_base_type.size == 1:
            # single-byte subranges use unsigned comparisons; integer (4-byte) subranges use signed comparisons.
            jump_less = "JB"
            jump_greater = "JA"
        else:
            jump_less = "JL"
            jump_greater = "JG"

        comment = "Validate we are within proper range"
        self.emit_code("CMP {}, {}".format(reg, subrange_base_type.range_min_int), comment)
        self.emit_jump_to_error(jump_less, "_PASCAL_SUBRANGE_ERROR")
        self.emit_code("CMP {}, {}".format(reg, subrange_base_type.range_max_int))
        self.emit_jump_to_error(jump_greater, "_PASCAL_SUBRANGE_ERROR")

    def generate_parameter_comments(self, block):
        assert isinstance(block, TACBlock)
        for param in block.parameter_list:
            local_symbol = block.symbol_table.fetch(param.symbol.name)
            self.emit_comment("Parameter {} - [{}]".format(param.symbol.name, local_symbol.memory_address), True)

    def generate_local_variable_comments(self, block):
        assert isinstance(block, TACBlock)
        for symbol_name in block.symbol_table.symbols.keys():
            if block.is_main or block.parameter_list.fetch(symbol_name) is None:
                local_symbol = block.symbol_table.symbols[symbol_name]
                if isinstance(local_symbol, Symbol):
                    if isinstance(local_symbol, FunctionResultVariableSymbol):
                        self.emit_comment("Function Result - [{}]".format(local_symbol.memory_address), True)
                    else:
                        self.emit_comment("Local Variable {} - [{}]".format(symbol_name, local_symbol.memory_address),
                                          True)

    def generate_array_variable_memory_allocation_code(self, symbol):
        assert isinstance(symbol, Symbol)
        assert isinstance(symbol.pascal_type, pascaltypes.ArrayType)
        self.emit_code("mov rdi, {}".format(symbol.pascal_type.num_items_in_array),
                       'Allocate memory for array {}'.format(symbol.name))
        self.emit_code("mov rsi, {}".format(symbol.pascal_type.component_type.size))
        self.used_calloc = True
        self.emit_code("call _PASCAL_ALLOCATE_MEMORY")
        self.emit_code("mov [{}], rax".format(symbol.memory_address))

    def generate_parameter_list_to_stack_code(self, block):
        assert isinstance(block, TACBlock)
        number_int_parameters = 0
        number_real_parameters = 0
        for parameter in block.parameter_list:
            local_symbol = block.symbol_table.fetch(parameter.symbol.name)
            # TODO - this will break when we have so many parameters that they will get
            # passed on the stack instead of in a register.
            if isinstance(parameter.symbol.pascal_type, pascaltypes.ArrayType):
                # array parameters are always the address of the array.  If it is by ref, the caller
                # will pass in the address of the original array.  If it is byval, the caller will copy
                # the array and provide the address of the copy.  In either case, we just move the
                # parameter to the stack as-is.
                number_int_parameters += 1
                parameter_register = integer_parameter_position_to_register(number_int_parameters)
                if parameter.is_by_ref:
                    comment = "Copy address of variable array parameter {} to stack"
                else:
                    comment = "Copy address of array parameter {} to stack"
                comment = comment.format(parameter.symbol.name)
                self.emit_code("mov [{}], {}".format(local_symbol.memory_address, parameter_register, comment))
            elif parameter.is_by_ref:
                number_int_parameters += 1
                parameter_register = integer_parameter_position_to_register(number_int_parameters)
                self.emit_code("mov [{}], {}".format(local_symbol.memory_address, parameter_register),
                               "Copy variable parameter {} to stack".format(parameter.symbol.name))
            elif isinstance(parameter.symbol.pascal_type, pascaltypes.RealType):
                parameter_register = "xmm{}".format(number_real_parameters)
                number_real_parameters += 1
                # the param memory address is one of the xmm registers.
                self.emit_code("movq [{}], {}".format(local_symbol.memory_address, parameter_register),
                               "Copy parameter {} to stack".format(parameter.symbol.name))
            else:
                # the param memory address is a register
                number_int_parameters += 1
                parameter_register = integer_parameter_position_to_register(number_int_parameters)
                register_slice = get_register_slice_by_bytes(parameter_register, parameter.symbol.pascal_type.size)
                self.emit_code("mov [{}], {}".format(local_symbol.memory_address, register_slice),
                               "Copy parameter {} to stack".format(parameter.symbol.name))

    def generate_procedure_or_function_call_code(self, block, node, parameters):
        assert isinstance(block, TACBlock)
        assert isinstance(node, TACCallFunctionNode)
        assert not isinstance(node, TACCallSystemFunctionNode)
        assert len(parameters) >= node.number_of_parameters
        local_parameter_list = parameters[(-1 * node.number_of_parameters):]
        number_integer_parameters = 0
        number_real_parameters = 0
        activation_symbol = block.symbol_table.parent.fetch(node.function_name)
        assert isinstance(activation_symbol, ActivationSymbol)
        assert node.number_of_parameters == len(activation_symbol.parameter_list)  # type mismatches are caught upstream

        # local_parameter_list has a list of TACParamNodes - that has information of what is going in.
        # activation_symbol.parameter_list has the information of where it goes

        arrays_to_free_after_proc_call = 0
        for parameter_position in range(0, node.number_of_parameters):
            # remember - pointers count as int parameters
            # "actual parameter" - term in the iso standard from e.g. 6.7.3.  Results of expressions/functions passed
            # into the function/procedure.  Formal parameter is the definition in the function designator.
            actual_parameter = local_parameter_list[parameter_position]
            formal_parameter = activation_symbol.parameter_list[parameter_position]
            assert isinstance(actual_parameter, TACParamNode)
            assert isinstance(formal_parameter, Parameter)

            if formal_parameter.is_by_ref:
                comment = "Parameter {} for {} ({}, ByRef)".format(formal_parameter.symbol.name,
                                                                   activation_symbol.name,
                                                                   str(formal_parameter.symbol.pascal_type.identifier))
            else:
                comment = "Parameter {} for {} ({})".format(formal_parameter.symbol.name,
                                                            activation_symbol.name,
                                                            str(formal_parameter.symbol.pascal_type.identifier))

            if formal_parameter.is_by_ref and actual_parameter.parameter_value.is_by_ref:
                # if the formal parameter is by ref and actual parameter is by ref, then just pass the
                # value of the actual parameter on through, as that value is a memory address.
                number_integer_parameters += 1
                assert number_integer_parameters <= 6
                register = integer_parameter_position_to_register(number_integer_parameters)
                self.emit_code("mov {}, [{}]".format(register, actual_parameter.parameter_value.memory_address),
                               comment)
            elif formal_parameter.is_by_ref and isinstance(formal_parameter.symbol.pascal_type, pascaltypes.ArrayType):
                # arrays are already references, so just pass the value of the actual parameter
                # on through, exactly same as the case above.
                number_integer_parameters += 1
                assert number_integer_parameters <= 6
                register = integer_parameter_position_to_register(number_integer_parameters)
                self.emit_code("mov {}, [{}]".format(register, actual_parameter.parameter_value.memory_address),
                               comment)
            elif formal_parameter.is_by_ref:
                number_integer_parameters += 1
                assert number_integer_parameters <= 6
                # pointers are 64-bit
                register = integer_parameter_position_to_register(number_integer_parameters)
                self.emit_code("LEA {}, [{}]".format(register, actual_parameter.parameter_value.memory_address),
                               comment)
            elif isinstance(formal_parameter.symbol.pascal_type, pascaltypes.ArrayType):
                # need to create a copy of the array and pass that in.
                assert isinstance(formal_parameter.symbol.pascal_type, pascaltypes.ArrayType)
                self.emit_code("PUSH RDI", "create copy of array {}".format(actual_parameter.parameter_value.name))
                self.emit_code("PUSH RSI")
                self.emit_code("MOV RDI, {}".format(formal_parameter.symbol.pascal_type.num_items_in_array))
                self.emit_code("MOV RSI, {}".format(formal_parameter.symbol.pascal_type.component_type.size))
                self.used_calloc = True
                self.emit_code("call _PASCAL_ALLOCATE_MEMORY")
                self.emit_code("POP RSI")
                self.emit_code("POP RDI")

                # rax has the pointer to the memory
                arrays_to_free_after_proc_call += 1
                self.emit_code("PUSH RAX", "store address of this array copy to free later")

                number_integer_parameters += 1
                assert number_integer_parameters <= 6, \
                    "AssemblyGenerator.generate_procedure_or_function_call_code: Cannot handle > 6 integer parameters"
                register = integer_parameter_position_to_register(number_integer_parameters)
                self.emit_code("MOV {}, RAX".format(register))
                self.emit_copy_memory(register, actual_parameter.parameter_value,
                                      formal_parameter.symbol.pascal_type.size, "", True)
            elif isinstance(formal_parameter.symbol.pascal_type, pascaltypes.IntegerType) or \
                    isinstance(formal_parameter.symbol.pascal_type, pascaltypes.BooleanType) or \
                    isinstance(formal_parameter.symbol.pascal_type, pascaltypes.CharacterType) or \
                    isinstance(formal_parameter.symbol.pascal_type, pascaltypes.SubrangeType) or \
                    isinstance(formal_parameter.symbol.pascal_type, pascaltypes.EnumeratedType):
                number_integer_parameters += 1
                assert number_integer_parameters <= 6, \
                    "AssemblyGenerator.generate_procedure_or_function_call_code: Cannot handle > 6 integer parameters"
                register = integer_parameter_position_to_register(number_integer_parameters)
                register_slice = get_register_slice_by_bytes(register, formal_parameter.symbol.pascal_type.size)
                self.emit_move_to_register_from_stack_or_literal(register_slice, actual_parameter.parameter_value,
                                                                 comment)
            elif isinstance(formal_parameter.symbol.pascal_type, pascaltypes.RealType):
                register = "xmm{}".format(number_real_parameters)
                number_real_parameters += 1
                assert number_real_parameters <= 8, \
                    "AssemblyGenerator.generate_procedure_or_function_call_code: Cannot handle > 8 real parameters"
                self.emit_move_to_xmm_register_from_stack(register, actual_parameter.parameter_value, comment)
            else:  # pragma: no cover
                raise ASMGeneratorError("Invalid Parameter Type")

        if arrays_to_free_after_proc_call % 2 > 0:
            self.emit_code("PUSH RAX",
                           "bogus push to keep stack aligned at 16-bit boundary before function call")

        self.emit_code("call {}".format(node.label), "call {}()".format(node.function_name))
        if activation_symbol.result_type is not None:
            # Need to insert code for the runtime error for function with undefined return_value
            self.runtime_errors[18].is_used = True

            # return value is now in either RAX or XMM0 - need to store it in right place
            comment = "assign return value of function to {}".format(node.left_value.name)
            if isinstance(activation_symbol.result_type, pascaltypes.IntegerType):
                self.emit_code("MOV [{}], EAX".format(node.left_value.memory_address), comment)
            elif isinstance(activation_symbol.result_type, pascaltypes.BooleanType):
                self.emit_code("MOV [{}], AL".format(node.left_value.memory_address), comment)
            else:
                self.emit_code("MOVSD [{}], XMM0".format(node.left_value.memory_address), comment)
        del parameters[(-1 * node.number_of_parameters):]

        if arrays_to_free_after_proc_call % 2 > 0:
            self.emit_code("POP RAX", "undo stack-alignment push from above")
            for i in range(arrays_to_free_after_proc_call):
                self.emit_code("POP RDI", "free memory from array value parameter")
                self.used_dispose = True
                self.emit_code("CALL _PASCAL_DISPOSE_MEMORY")

    def generate_state_validation_code_for_file_variable(self, file_symbol, state):
        global FILE_STATE_GENERATION
        global FILE_STATE_INSPECTION
        global FILE_STATE_NOT_INITIALIZED
        assert isinstance(file_symbol, Symbol)
        assert isinstance(file_symbol.pascal_type, pascaltypes.FileType)
        assert state in (FILE_STATE_GENERATION, FILE_STATE_INSPECTION)

        # current state of the file is in the 9th byte after the location of the file
        self.emit_code("lea rax, [{}]".format(file_symbol.memory_address), "validate file state")
        self.emit_code("add rax, 8")
        self.emit_code("mov r11b, byte [rax]")
        self.emit_code("test r11b, r11b")
        self.emit_jump_to_error("jz", "_PASCAL_FILE_UNDEFINED_ERROR")
        self.emit_code("cmp r11b, {}".format(str(state)))
        if state == FILE_STATE_GENERATION:
            self.emit_jump_to_error("jne", "_PASCAL_FILE_NOT_GENERATION_MODE_ERROR")
        else:
            self.emit_jump_to_error("jne", "_PASCAL_FILE_NOT_INSPECTION_MODE_ERROR")

    def generate_initialization_code_for_program_parameter(self):
        # assumption:
        # RDI - contains int argc (integer with number parameters)
        # RSI - contains char **argv

        symbol_list = []

        for symbol_name in self.tac_generator.global_symbol_table.symbols.keys():
            tac_symbol = self.tac_generator.global_symbol_table.fetch(symbol_name)
            if isinstance(tac_symbol, ProgramParameterSymbol) and tac_symbol.name not in ("input", "output"):
                symbol_list.append((tac_symbol.position, tac_symbol.filename_memory_address, tac_symbol.name))

        if len(symbol_list) > 0:
            self.emit_code("cmp RDI, {}".format(len(symbol_list)), "Test number of command-line arguments")
            self.emit_jump_to_error("jl", "_PASCAL_INSUFFICIENT_ARGC_ERROR")
            for symbol_info_tuple in symbol_list:
                rsi_offset = 8 * symbol_info_tuple[0]
                comment = "retrieve file name for variable {}".format(symbol_info_tuple[2])
                self.emit_code("mov RAX, [RSI+{}]".format(rsi_offset), comment)
                self.emit_code("mov [{}], rax".format(symbol_info_tuple[1]))

    def generate_initialization_code_for_global_file(self):
        # set up stdin and stdout if needed
        for symbol in self.tac_generator.global_symbol_table.symbols.values():
            if isinstance(symbol, ProgramParameterSymbol):

                if symbol.name == "output":
                    standard_in_or_out = "stdout"
                    starting_file_state = FILE_STATE_GENERATION
                elif symbol.name == "input":
                    standard_in_or_out = "stdin"
                    starting_file_state = FILE_STATE_INSPECTION
                else:
                    standard_in_or_out = ""
                    starting_file_state = FILE_STATE_NOT_INITIALIZED

                if symbol.name in ("input", "output"):
                    comment = "initialize global textfile variable '{}'".format(symbol.name)
                    self.emit_code("lea r11, [rel {}]".format(standard_in_or_out), comment)
                    self.emit_code("mov rax, [r11]")
                    self.emit_code("mov [{}], rax".format(symbol.memory_address))

                self.emit_code("lea rax, [{}]".format(symbol.memory_address))
                self.emit_code("add rax, 8")
                self.emit_code("mov [rax], byte {}".format(starting_file_state))
                self.emit_code("inc rax")
                self.emit_code("mov [rax], byte 0")

    def generate_code(self):
        parameter_stack = []  # this is a stack of parameters

        for block in self.tac_generator.tac_blocks_list:
            assert isinstance(block, TACBlock)

            if block.is_main:
                self.emit_label("main")
                tac_node_list = block.tacnodes
            else:
                self.emit_label(block.tacnodes[0].label.name, block.tacnodes[0].comment)
                tac_node_list = block.tacnodes[1:]

            total_storage_needed_bytes = 0  # measured in bytes

            for symbol in block.symbol_table.symbols.values():
                if isinstance(symbol, Symbol):
                    if symbol.memory_address is None:
                        # to ensure stack alignment, we subtract 8 bytes from the stack even if we're putting in
                        # a 1, 2, or 4 byte value.
                        total_storage_needed_bytes += 8
                        symbol.memory_address = "RBP-{}".format(str(total_storage_needed_bytes))
                    if isinstance(symbol, ProgramParameterSymbol) and symbol.name not in ("input", "output"):
                        total_storage_needed_bytes += 8

            if total_storage_needed_bytes > 0 or block.is_main:
                self.emit_code("PUSH RBP")  # ABI requires callee to preserve RBP
                self.emit_code("MOV RBP, RSP", "save stack pointer")
                # X86-64 ABI requires stack to stay aligned to 16-byte boundary.  Make sure we subtract in chunks of 16
                # if we are in main.  If we are in a called function, we will begin with the stack 8-bytes off because
                # of the 8-byte return address pushed onto the stack.  However, the first thing we do is push RBP
                # which then gets us back to 16-byte alignment.
                # If we are ever out of alignment, we will segfault calling printf() with XMM registers

                if total_storage_needed_bytes % 16 > 0:
                    total_storage_needed_bytes += 16 - (total_storage_needed_bytes % 16)
                self.emit_code("SUB RSP, " + str(total_storage_needed_bytes), "allocate local storage")
                if not block.is_main:
                    self.generate_parameter_comments(block)
                    self.generate_local_variable_comments(block)
                    self.generate_parameter_list_to_stack_code(block)

                    # allocate space for local variable arrays
                    for symbol_name in block.symbol_table.symbols.keys():
                        if block.parameter_list.fetch(symbol_name) is None:
                            local_symbol = block.symbol_table.symbols[symbol_name]
                            if isinstance(local_symbol, Symbol) and not isinstance(local_symbol,
                                                                                   FunctionResultVariableSymbol):
                                if isinstance(local_symbol.pascal_type, pascaltypes.ArrayType):
                                    self.generate_array_variable_memory_allocation_code(local_symbol)

                else:
                    self.generate_local_variable_comments(block)
                    # This needs to be first because it takes advantage of RDI and RSI state when execution starts
                    self.generate_initialization_code_for_program_parameter()
                    self.generate_initialization_code_for_global_file()
                    if self.used_x87_code:
                        self.emit_code("finit")
                    # need to init any global variables that are arrays
                    for symbol in self.tac_generator.global_symbol_table.symbols.values():
                        if isinstance(symbol, Symbol) and isinstance(symbol.pascal_type, pascaltypes.ArrayType):
                            self.generate_array_variable_memory_allocation_code(symbol)

            for node in tac_node_list:
                if isinstance(node, TACCommentNode):
                    self.emit_comment(node.comment)
                elif isinstance(node, TACLabelNode):
                    self.emit_label(node.label.name, node.comment)
                elif isinstance(node, TACGotoNode):
                    self.emit_code("jmp {}".format(node.label.name))
                elif isinstance(node, TACIFZNode):
                    self.emit_code("mov al, [{}]".format(node.value.memory_address))
                    self.emit_code("test al,al")
                    self.emit_code("jz {}".format(node.label.name))
                elif isinstance(node, TACParamNode):
                    parameter_stack.append(node)
                elif isinstance(node, TACFunctionReturnNode):
                    if isinstance(node.return_value, Symbol):
                        # do the function returning stuff here
                        # the "ret" itself is emitted below.
                        # TODO - Detect if the return value was not set, and error if it wasn't.
                        if isinstance(node.return_value.pascal_type, pascaltypes.IntegerType):
                            self.emit_code("mov EAX, [{}]".format(node.return_value.memory_address),
                                           "set up return value")
                        elif isinstance(node.return_value.pascal_type, pascaltypes.BooleanType):
                            # whereas mov EAX, [{}] will zero out the high 32 bits of RAX, moving AL will not.
                            self.emit_code("movzx RAX, BYTE [{}]".format(node.return_value.memory_address),
                                           "set up return value")
                        else:
                            self.emit_code("movsd XMM0, [{}]".format(node.return_value.memory_address),
                                           "set up return value")
                elif isinstance(node, TACUnaryNode):
                    if node.operator == TACOperator.INT_TO_REAL:
                        assert node.argument.pascal_type.size in [1, 2, 4, 8]
                        if node.argument.pascal_type.size in (1, 2):
                            raise ASMGeneratorError("Cannot handle 8- or 16-bit int convert to real")
                        elif node.argument.pascal_type.size == 4:
                            # extend to 8 bytes
                            self.emit_move_to_register_from_stack("eax", node.argument)
                            self.emit_code("cdqe")
                        else:
                            self.emit_move_to_register_from_stack("rax", node.argument)
                        # rax now has the value we need to convert to the float
                        comment = "convert {} to real, store result in {}".format(node.argument.name,
                                                                                  node.left_value.name)
                        self.emit_code("cvtsi2sd xmm0, rax", comment)
                        # now save the float into its location
                        self.emit_move_to_stack_from_xmm_register(node.left_value, "xmm0")
                    elif node.operator == TACOperator.ASSIGN:
                        if isinstance(node.left_value.pascal_type, pascaltypes.ArrayType):
                            assert node.left_value.pascal_type.size == node.argument.pascal_type.size or \
                                   (node.left_value.pascal_type.is_string_type() and
                                    isinstance(node.argument.pascal_type, pascaltypes.StringLiteralType))
                            comment = "Copy array {} into {}".format(node.argument.name, node.left_value.name)
                            self.emit_copy_memory(node.left_value, node.argument, node.left_value.pascal_type.size,
                                                  comment, False)
                        else:
                            reg = get_register_slice_by_bytes("RAX", node.left_value.pascal_type.size)
                            # first, get the argument into reg.  If argument is a by ref parameter, we need to
                            # dereference the pointer.
                            comment = "Move {} into {}".format(node.argument.name, node.left_value.name)
                            self.emit_move_to_register_from_stack(reg, node.argument, comment)
                            if isinstance(node.left_value.pascal_type, pascaltypes.SubrangeType):
                                # need to validate that the value is in the range before assigning it
                                self.generate_subrange_test_code(reg, node.left_value.pascal_type)
                            # now, get the value from reg into left_value.  If left_value is a by ref parameter, we
                            # need to dereference the pointer.
                            self.emit_move_to_stack_from_register(node.left_value, reg)
                    elif node.operator == TACOperator.ASSIGN_ADDRESS_OF:
                        assert isinstance(node.left_value.pascal_type, pascaltypes.PointerType)
                        comment = "Move address of {} into {}".format(node.argument.name, node.left_value.name)
                        self.emit_move_address_to_register_from_stack("RAX", node.argument, comment)
                        self.emit_move_to_stack_from_register(node.left_value, "RAX")
                    elif node.operator == TACOperator.ASSIGN_TO_DEREFERENCE:
                        assert isinstance(node.left_value.pascal_type, pascaltypes.PointerType)
                        if isinstance(node.argument.pascal_type, pascaltypes.ArrayType):
                            assert node.left_value.pascal_type.points_to_type.size == node.argument.pascal_type.size
                            comment = "Copy array {} into {}".format(node.argument.name, node.left_value.name)
                            self.emit_copy_memory(node.left_value, node.argument, node.argument.pascal_type.size,
                                                  comment, False)
                        else:
                            comment = "Mov {} to address contained in {}".format(node.argument.name,
                                                                                 node.left_value.name)
                            # Note - this works with reals just fine, because we will movsd into a xmm register
                            # before doing anything with them.
                            reg = get_register_slice_by_bytes("R11", node.argument.pascal_type.size)
                            self.emit_move_to_register_from_stack(reg, node.argument, comment)
                            self.emit_code("MOV R10, [{}]".format(node.left_value.memory_address))
                            self.emit_code("MOV [R10], {}".format(reg))
                    elif node.operator == TACOperator.ASSIGN_DEREFERENCE_TO:
                        assert isinstance(node.argument.pascal_type, pascaltypes.PointerType)
                        comment = "Mov dereference of {} to {}".format(node.argument.name, node.left_value.name)
                        destination_register = get_register_slice_by_bytes("RAX", node.left_value.pascal_type.size)
                        self.emit_move_dereference_to_register_from_stack(destination_register, node.argument, comment)
                        self.emit_move_to_stack_from_register(node.left_value, destination_register)
                    elif node.operator == TACOperator.NOT:
                        assert isinstance(node.argument.pascal_type, pascaltypes.BooleanType)
                        assert isinstance(node.left_value.pascal_type, pascaltypes.BooleanType)
                        self.emit_move_to_register_from_stack("AL", node.argument)
                        self.emit_code("NOT AL")
                        self.emit_code("AND AL, 0x01")
                        self.emit_move_to_stack_from_register(node.left_value, "AL")

                    else:  # pragma: no cover
                        raise ASMGeneratorError("Invalid operator: {}".format(node.operator))
                elif isinstance(node, TACUnaryLiteralNode):
                    if isinstance(node.literal, StringLiteral):
                        # dealing with PEP8 line length
                        glt = self.tac_generator.global_literal_table
                        literal_address = glt.fetch(node.literal.value, pascaltypes.StringLiteralType()).memory_address
                        comment = "Move literal '{}' into {}".format(node.literal.value, node.left_value.name)
                        self.emit_code("lea rax, [rel {}]".format(literal_address), comment)
                        self.emit_move_to_stack_from_register(node.left_value, "rax")
                    elif isinstance(node.literal, RealLiteral):
                        glt = self.tac_generator.global_literal_table
                        literal_address = glt.fetch(node.literal.value, pascaltypes.RealType()).memory_address
                        comment = "Move literal {} into {}".format(node.literal.value, node.left_value.name)
                        self.emit_code("movsd xmm0, [rel {}]".format(literal_address), comment)
                        self.emit_move_to_stack_from_xmm_register(node.left_value, "xmm0")
                    else:
                        if node.operator == TACOperator.ASSIGN:
                            comment = "Move literal '{}' into {}".format(node.literal.value, node.left_value.name)
                            # putting the result into rax to use existing helper function vs. special casing this here.
                            if isinstance(node.literal, CharacterLiteral):
                                val = ord(node.literal.value)
                            else:
                                val = node.literal.value
                            register_slice = get_register_slice_by_bytes("RAX", node.left_value.pascal_type.size)
                            self.emit_code("mov {}, {}".format(register_slice, val), comment)
                            self.emit_move_to_stack_from_register(node.left_value, register_slice)
                        elif node.operator == TACOperator.INT_TO_REAL:
                            assert isinstance(node.literal, IntegerLiteral)
                            comment = "Move integer literal {} into real symbol {}".format(node.literal.value,
                                                                                           node.left_value.name)
                            self.emit_code("MOV EAX, {}".format(node.literal.value), comment)
                            self.emit_code("CDQE")
                            self.emit_code("cvtsi2sd xmm0, rax")
                            # now save the float into its location
                            self.emit_move_to_stack_from_xmm_register(node.left_value, "xmm0")
                        elif node.operator == TACOperator.ASSIGN_TO_DEREFERENCE:
                            assert isinstance(node.left_value.pascal_type, pascaltypes.PointerType)
                            assert isinstance(node.left_value.pascal_type.points_to_type, pascaltypes.IntegerType)
                            comment = "Move integer literal {} into address contained in {}"
                            comment = comment.format(node.literal.value, node.left_value.name)
                            self.emit_code("MOV R10, [{}]".format(node.left_value.memory_address), comment)
                            self.emit_code("MOV [R10], DWORD {}".format(node.literal.value))

                        else:  # pragma: no cover
                            raise ASMGeneratorError("Invalid operator: {}".format(repr(node.operator)))

                elif isinstance(node, TACCallFunctionNode) and \
                        not isinstance(node, TACCallSystemFunctionNode):
                    self.generate_procedure_or_function_call_code(block, node, parameter_stack)

                elif isinstance(node, TACCallSystemFunctionNode):
                    if node.label.name[:6] == "_WRITE":
                        if node.label.name == "_WRITE_LINE_FEED":
                            output_file_symbol = parameter_stack[-1].parameter_value
                            self.generate_state_validation_code_for_file_variable(output_file_symbol,
                                                                                  FILE_STATE_GENERATION)
                            assert node.number_of_parameters == 1
                            self.emit_code("mov rdi, [{}]".format(output_file_symbol.memory_address))
                            self.emit_code("lea rsi, [rel _printf_line_feed]")
                            self.emit_code("mov rax, 0")
                            self.emit_code("call fprintf wrt ..plt")
                            self.emit_code("XOR RDI, RDI", "Flush standard output when we do a writeln")
                            self.emit_code("CALL fflush wrt ..plt")
                            self.emit_code("")
                            del parameter_stack[-1]
                        else:
                            assert node.number_of_parameters == 2
                            output_file_symbol = parameter_stack[-2].parameter_value
                            self.generate_state_validation_code_for_file_variable(output_file_symbol,
                                                                                  FILE_STATE_GENERATION)
                            output_parameter_symbol = parameter_stack[-1].parameter_value
                            if node.label.name == "_WRITE_INTEGER":
                                self.emit_code("mov rdi, [{}]".format(output_file_symbol.memory_address))
                                self.emit_code("lea rsi, [rel _printf_integer_format]")
                                destination_register = get_register_slice_by_bytes("RDX",
                                                                                   output_parameter_symbol.
                                                                                   pascal_type.size)
                                self.emit_move_to_register_from_stack_or_literal(destination_register,
                                                                                 output_parameter_symbol)
                                # must pass 0 (in rax) as number of floating point args since fprintf is variadic
                                self.emit_code("mov rax, 0")
                                self.emit_code("call fprintf wrt ..plt")
                            elif node.label.name == "_WRITE_REAL":
                                self.emit_code("mov rdi, [{}]".format(output_file_symbol.memory_address))
                                self.emit_code("lea rsi, [rel _printf_real_format]")
                                self.emit_move_to_xmm_register_from_stack("xmm0", output_parameter_symbol)
                                self.emit_code("mov rax, 1", "1 floating point param")
                                self.emit_code("call fprintf wrt ..plt")
                            elif node.label.name == "_WRITE_STRING_LITERAL":
                                assert isinstance(output_parameter_symbol, ConstantSymbol), (
                                    "Constant expected, saw {}".format(type(output_parameter_symbol)))
                                self.emit_code("mov rdi, [{}]".format(output_file_symbol.memory_address))
                                self.emit_code("mov rsi, [{}]".format(output_parameter_symbol.memory_address))
                                self.emit_code("mov edx, {}".format(len(output_parameter_symbol.value)))
                                self.emit_code("call _PASCAL_PRINT_STRING_TYPE wrt ..plt", "in compiler2_system_io.asm")
                            elif node.label.name == "_WRITE_STRING":
                                assert isinstance(output_parameter_symbol, Symbol)
                                assert output_parameter_symbol.pascal_type.is_string_type()
                                self.emit_code("mov rdi, [{}]".format(output_file_symbol.memory_address))
                                self.emit_code("mov rsi, [{}]".format(output_parameter_symbol.memory_address))
                                self.emit_code(
                                    "mov edx, {}".format(output_parameter_symbol.pascal_type.num_items_in_array))
                                self.emit_code("call _PASCAL_PRINT_STRING_TYPE wrt ..plt", "in compiler2_system_io.asm")
                            elif node.label.name == "_WRITE_CHARACTER":
                                self.emit_move_to_register_from_stack("RDI", output_parameter_symbol)
                                self.emit_code("mov rsi, [{}]".format(output_file_symbol.memory_address))
                                self.emit_code("call fputc wrt ..plt")
                            elif node.label.name == "_WRITE_BOOLEAN":
                                self.emit_move_to_register_from_stack("al", output_parameter_symbol)
                                self.emit_code("test al, al")
                                false_label = self.get_next_label()
                                print_label = self.get_next_label()
                                self.emit_code("je {}".format(false_label))
                                self.emit_code("lea rsi, [rel _printf_true]")
                                self.emit_code("mov edx, 4")
                                self.emit_code("jmp {}".format(print_label))
                                self.emit_label(false_label)
                                self.emit_code("lea rsi, [rel _printf_false]")
                                self.emit_code("mov edx, 5")
                                self.emit_label(print_label)
                                self.emit_code("mov rdi, [{}]".format(output_file_symbol.memory_address))
                                self.emit_code("call _PASCAL_PRINT_STRING_TYPE wrt ..plt", "in compiler2_system_io.asm")
                            del parameter_stack[-2:]
                    elif node.label.name == "_REWRITE":
                        assert node.number_of_parameters == 1
                        output_file_symbol = parameter_stack[-1].parameter_value
                        assert output_file_symbol.name not in ("input",
                                                               "output")  # these errors are raised in tac-ir.py

                        # TODO goes away when we add temporary files
                        assert isinstance(output_file_symbol, ProgramParameterSymbol)

                        # TODO much of these long strings of assembly in this function can be pulled out and this
                        # made easier to manage

                        reopen_label = self.get_next_label()
                        done_label = self.get_next_label()
                        self.emit_code("lea rax, [{}]".format(output_file_symbol.memory_address))
                        self.emit_code("add rax, 8")
                        self.emit_code("mov r11b, byte [rax]", "file state is in r11b")

                        # For FOPEN - RDI gets pointer to filename, RSI gets "w"
                        # For FREOPEN - RDI gets pointer to filename, RSI gets "w", RDX gets the FILE*
                        self.emit_code("mov rdi, [{}]".format(output_file_symbol.filename_memory_address))
                        # TODO gets more complicated when we can write binary
                        self.emit_code("lea rsi, [rel _filemode_write]")
                        self.emit_code("test r11b, r11b", "determine if we need to open or reopen this file")
                        self.emit_code("jg {}".format(reopen_label))
                        self.emit_code("call fopen wrt ..plt", "FILE* is in RAX")
                        self.emit_code("jmp {}".format(done_label))
                        self.emit_label(reopen_label)
                        self.emit_code("mov rdx, [{}]".format(output_file_symbol.memory_address))
                        self.emit_code("call freopen wrt ..plt", "FILE* is in RAX")
                        self.emit_label(done_label)
                        self.emit_code("test rax, rax")
                        self.emit_jump_to_error("jz", "_PASCAL_FILE_OPEN_ERROR")
                        self.emit_code("lea r11, [{}]".format(output_file_symbol.memory_address))
                        self.emit_code("mov [r11], rax")
                        self.emit_code("add r11, 8")
                        self.emit_code("mov [r11], byte {}".format(FILE_STATE_GENERATION))
                        del parameter_stack[-1]
                    elif node.label.name == "_SQRT_REAL":
                        comment = "parameter {} for sqrt()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_xmm_register_from_stack("xmm0", parameter_stack[-1].parameter_value, comment)
                        self.emit_code("xorps xmm8, xmm8", "validate parameter is >= 0")
                        self.emit_code("ucomisd xmm0, xmm8")
                        self.emit_jump_to_error("jb", "_PASCAL_SQRT_ERROR")
                        self.emit_code("sqrtsd xmm0, xmm0", 'sqrt()')
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        # Currently all the system functions use a temporary, which I know is not by ref.
                        # So, technically it would be quicker to do this:
                        # self.emit_code("MOVSD [{}], XMM0".format(node.left_value.memory_address), comment)
                        # however, to future-proof this for optimizations, I'll use the move_to_stack() functions
                        self.emit_move_to_stack_from_xmm_register(node.left_value, "XMM0", comment)
                    elif node.label.name in ("_SIN_REAL", "_COS_REAL"):
                        self.used_x87_code = True
                        comment = "parameter {} for sin()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_xmm_register_from_stack("xmm0", parameter_stack[-1].parameter_value, comment)
                        # sin() and cos() use the legacy x87 FPU.  This is slow but also very few instructions
                        # so easy for the compiler writer.  In x86-64 one is supposed to use library functions
                        # for this, but this is faster to code.
                        # Cannot move directly from xmm0 to the FPU stack; cannot move directly from a standard
                        # register to the FPU stack.  Can only move from memory
                        self.emit_code("movsd [{}], xmm0".format(node.left_value.memory_address),
                                       "use {} to move value to FPU".format(node.left_value.name))
                        self.emit_code("fld qword [{}]".format(node.left_value.memory_address))
                        self.emit_code("f{}".format(node.label.name[1:4]).lower())  # will generate fsin or fcos
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        # TODO - see comment to _SQRT_REAL where I use the move_to_stack() functions.  Technically
                        # there should be a test for node.left_value.is_by_ref here, but for now I know it has to be
                        # a local temporary, not a by ref parameter, so this is safe.  I don't want to write
                        # a fstp equivalent for that function when I don't need it.
                        self.emit_code("fstp qword [{}]".format(node.left_value.memory_address), comment)
                    elif node.label.name == "_ARCTAN_REAL":
                        self.used_x87_code = True
                        comment = "parameter {} for arctan()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_xmm_register_from_stack("xmm0", parameter_stack[-1].parameter_value, comment)
                        # sin() and cos() use the legacy x87 FPU.  This is slow but also very few instructions
                        # so easy for the compiler writer.  In x86-64 one is supposed to use library functions
                        # for this, but this is faster to code.
                        # Cannot move directly from xmm0 to the FPU stack; cannot move directly from a standard
                        # register to the FPU stack.  Can only move from memory
                        self.emit_code("movsd [{}], xmm0".format(node.left_value.memory_address),
                                       "use {} to move value to FPU".format(node.left_value.name))
                        self.emit_code("fld qword [{}]".format(node.left_value.memory_address))
                        # Pascal uses atan but x87 uses atan2.
                        self.emit_code("fld1")
                        self.emit_code("fpatan")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        # TODO - see comment to _SQRT_REAL where I use the move_to_stack() functions.  Technically
                        # there should be a test for node.left_value.is_by_ref here, but for now I know it has to be
                        # a local temporary, not a by_ref parameter, so this is safe.  I don't want to write
                        # a fstp equivalent for that function when I don't need it.
                        self.emit_code("fstp qword [{}]".format(node.left_value.memory_address), comment)
                    elif node.label.name == '_LN_REAL':
                        self.used_x87_code = True
                        comment = "parameter {} for ln()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_xmm_register_from_stack("xmm0", parameter_stack[-1].parameter_value, comment)
                        # ln() also uses the legacy x87 FPU.  The legacy FPU has a command for log base 2.
                        # Can get log in any other base from log base 2 by multiplying by the right factor
                        # FYL2X computes the Log base 2 of the value in ST0 and multiplies it by the value
                        # in ST1.  ln(x) = log base 2 of x / log base 2 of e
                        # which in turn equals log base 2 of x * ln 2.
                        self.emit_code("movsd [{}], xmm0".format(node.left_value.memory_address),
                                       "use {} to move value to FPU".format(node.left_value.name))
                        self.emit_code("xorps xmm8, xmm8", "validate parameter is > 0")
                        self.emit_code("ucomisd xmm0, xmm8")
                        self.emit_jump_to_error("jbe", "_PASCAL_LN_ERROR")
                        self.emit_code("FLDLN2")
                        self.emit_code("FLD QWORD [{}]".format(node.left_value.memory_address))
                        self.emit_code("FYL2X")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_code("fstp qword [{}]".format(node.left_value.memory_address), comment)
                    elif node.label.name == '_EXP_REAL':
                        self.used_x87_code = True
                        comment = "parameter {} for exp()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_xmm_register_from_stack("xmm0", parameter_stack[-1].parameter_value, comment)
                        # The code that I got from https://stackoverflow.com/questions/44957136
                        # and http://www.ray.masmcode.com/tutorial/fpuchap11.htm worked in many cases but not all.
                        # Used ChatGPT to assist with this version.

                        self.emit_code("movsd [{}], xmm0".format(node.left_value.memory_address),
                                       "use {} to move value to FPU".format(node.left_value.name))
                        self.emit_code("FLD QWORD [{}]".format(node.left_value.memory_address))

                        # compute y = x * log2(e)
                        self.emit_code("FLDL2E")  # ST0 = log2(e), ST1 = x
                        self.emit_code("FMULP ST1, ST0")  # ST0 = x * log2(e) = y

                        # split y into integer n and fractional f
                        self.emit_code("FLD ST0")  # ST0 = y, ST1 = y
                        self.emit_code("FRNDINT")  # ST0 = n (rounded y), ST1 = y
                        self.emit_code("FSUB ST1, ST0")  # ST1 = y-n = f, ST0 = n
                        self.emit_code("FXCH ST1")  # ST0 = y-n = f, ST1 = n

                        # compute 2^f using f2xm1
                        self.emit_code("F2XM1")  # ST0 = 2^f - 1, ST1 = n
                        self.emit_code("FLD1")  # ST0 = 1, ST1 = 2^f - 1, ST2 = n
                        self.emit_code("FADDP ST1, ST0")  # ST0 = 2^f, ST1 = n

                        # scale by 2^n: result = 2^(n+f) = e^x
                        self.emit_code("FSCALE")  # Per the fpuchap11.htm link above, FSCALE multiplies ST0 by
                        # 2^(ST1), first truncating ST1 to an integer.  It leaves ST1 intact.
                        # ST0 has 2^remainder of (x * log2(e)) * 2^integer part of (x*log2(e))
                        # So ST0 has e^x in it.  Neat.  ST1 still has x * log2(e) in it.
                        self.emit_code("FSTP ST1")  # We need to clean up the stack, so this gets rid of ST1
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_code("fstp qword [{}]".format(node.left_value.memory_address), comment)
                    elif node.label.name == "_ABS_REAL":
                        # There is an X87 abs() call, but that is slow.  So here is the logic:
                        # To find abs(x) we take x, and compare it to 0-x (which is the negative of x) and then
                        # return whichever is the largest.
                        comment = "parameter {} for abs()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_xmm_register_from_stack("xmm0", parameter_stack[-1].parameter_value, comment)
                        self.emit_code("xorps xmm8, xmm8")
                        self.emit_code("subsd xmm8, xmm0")
                        self.emit_code("maxsd xmm0, xmm8")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_xmm_register(node.left_value, "XMM0", comment)
                    elif node.label.name == "_ABS_INTEGER":
                        # There is no X86 ABS() call.  There is a slow way where you test the value, compare to zero
                        # then if it's >= than zero jump ahead, and if it's less than zero, negate it.  Jumping makes
                        # code execution very slow.  This is the way CLang 7.0 handles abs() with -O3 enabled
                        comment = "parameter {} for abs()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_register_from_stack_or_literal("eax", parameter_stack[-1].parameter_value,
                                                                         comment)
                        self.emit_code("mov r11d, eax")
                        self.emit_code("neg eax")  # neg sets the FLAGS
                        self.emit_code("cmovl eax, r11d")  # if neg eax made eax less than zero, move r11d into eax
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_register(node.left_value, "EAX", comment)
                    elif node.label.name == '_ODD_INTEGER':
                        # per 6.6.6.5 of the ISO Standard, the ODD() function is defined as returning true
                        # if (abs(x) mod 2) = 1.  We could have the TAC simplify ODD into calling ABS but that would
                        # mean two function calls and they are slow.  So for now we will copy the logic for ABS and
                        # mod in here manually.  Note that fortunately the mod equals 0 or 1 at the end, and
                        # that means we do not need a jump test.
                        comment = "parameter {} for odd()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_register_from_stack_or_literal("eax", parameter_stack[-1].parameter_value,
                                                                         comment)
                        self.emit_code("mov r11d, eax", "odd() is 'if ABS(x) mod 2 == 1")
                        self.emit_code("neg eax")  # neg sets the FLAGS
                        self.emit_code("cmovl eax, r11d")  # if neg eax made eax less than zero, move r11d into eax
                        self.emit_code("cdq", "sign extend eax -> edx:eax")
                        self.emit_code("mov r11d, 2")
                        self.emit_code("idiv r11d")
                        self.emit_code("mov al, dl", "remainder of idiv is in edx; must be 0 or 1. Take lowest 8 bits")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_register(node.left_value, "AL", comment)
                    elif node.label.name == "_SQR_REAL":
                        # easy - multiply the value by itself
                        # TODO - test for INF since that would be an error, and per ISO standard we need to exit
                        comment = "parameter {} for sqr()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_xmm_register_from_stack("xmm0", parameter_stack[-1].parameter_value, comment)
                        self.emit_code("mulsd xmm0, xmm0")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_xmm_register(node.left_value, "XMM0", comment)
                    elif node.label.name == "_SQR_INTEGER":
                        # similarly easy - multiply the value by itself
                        comment = "parameter {} for sqr()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_register_from_stack_or_literal("eax", parameter_stack[-1].parameter_value,
                                                                         comment)
                        self.emit_code("imul eax, eax")
                        self.emit_jump_to_error("jo", "_PASCAL_OVERFLOW_ERROR")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_register(node.left_value, "EAX", comment)
                    elif node.label.name == "_CHR_INTEGER":
                        comment = "parameter {} for chr()".format(str(parameter_stack[-1].parameter_value))
                        self.emit_move_to_register_from_stack_or_literal("R11D", parameter_stack[-1].parameter_value,
                                                                         comment)
                        self.emit_code("CMP R11D, 0")
                        self.emit_jump_to_error("JL", "_PASCAL_CHR_ERROR")
                        self.emit_code("CMP R11D, 255")
                        self.emit_jump_to_error("JG", "_PASCAL_CHR_ERROR")
                        self.emit_code("MOV AL, R11B", "take least significant 8 bits")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_register(node.left_value, "AL", comment)
                    elif node.label.name == "_ORD_ORDINAL":
                        # Returns the integer representation of the ordinal type.  Since under the covers,
                        # ordinal types are stored as integers, this is just returning itself.
                        # Trick is that the ordinal type may be 1 byte (boolean, character, or user-defined ordinal)
                        # or 4 bytes (integer).  If it's one byte, we need to zero-extend it.
                        assert parameter_stack[-1].parameter_value.pascal_type.size in (1, 4)

                        comment = "parameter {} for ord()".format(str(parameter_stack[-1].parameter_value))
                        if parameter_stack[-1].parameter_value.pascal_type.size == 1:
                            # TODO - this can easily be done in a single mov statement of the form
                            # movzx EAX, byte [rbp-8]
                            # or whatever - but need to decide whether it's worth hacking up
                            # emit_move_to_register_from_stack to handle this one-off.
                            self.emit_move_to_register_from_stack("R11B", parameter_stack[-1].parameter_value, comment)
                            self.emit_code("MOVZX EAX, R11B")
                        else:
                            self.emit_move_to_register_from_stack_or_literal("EAX", parameter_stack[-1].parameter_value)
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_register(node.left_value, "EAX", comment)
                    elif node.label.name == "_SUCC_ORDINAL":
                        assert parameter_stack[-1].parameter_value.pascal_type.size in (1, 4)
                        assert node.left_value.pascal_type.size == parameter_stack[-1].parameter_value.pascal_type.size
                        comment = "parameter {} for succ()".format(str(parameter_stack[-1].parameter_value))
                        reg = get_register_slice_by_bytes("RAX", node.left_value.pascal_type.size)
                        bt = parameter_stack[-1].parameter_value.pascal_type

                        self.emit_move_to_register_from_stack_or_literal(reg, parameter_stack[-1].parameter_value,
                                                                         comment)

                        if isinstance(bt, pascaltypes.CharacterType):
                            self.emit_code("CMP {}, 255".format(reg))
                            self.emit_jump_to_error("JE", "_PASCAL_SUCC_PRED_ERROR")  # cannot increment a char past 255

                        self.emit_code("INC {}".format(reg))

                        if isinstance(bt, pascaltypes.IntegerType):
                            self.emit_jump_to_error("jo", "_PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.BooleanType):
                            self.emit_code("CMP {}, 1".format(reg))
                            self.emit_jump_to_error("JG", "_PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.SubrangeType):
                            self.generate_subrange_test_code(reg, bt)
                        elif isinstance(bt, pascaltypes.CharacterType):
                            pass  # did the test for overflow above.
                        else:
                            assert isinstance(bt, pascaltypes.EnumeratedType)
                            self.emit_code("CMP {}, {}".format(reg, str(len(bt.value_list))))
                            self.emit_jump_to_error("JGE", "_PASCAL_SUCC_PRED_ERROR")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_register(node.left_value, reg, comment)
                    elif node.label.name == "_PRED_ORDINAL":
                        assert parameter_stack[-1].parameter_value.pascal_type.size in (1, 4)
                        assert node.left_value.pascal_type.size == parameter_stack[-1].parameter_value.pascal_type.size
                        comment = "parameter {} for pred()".format(str(parameter_stack[-1].parameter_value))
                        reg = get_register_slice_by_bytes("RAX", node.left_value.pascal_type.size)

                        self.emit_move_to_register_from_stack_or_literal(reg, parameter_stack[-1].parameter_value,
                                                                         comment)
                        self.emit_code("DEC {}".format(reg))
                        bt = parameter_stack[-1].parameter_value.pascal_type
                        if isinstance(bt, pascaltypes.IntegerType):
                            self.emit_jump_to_error("jo", "_PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.SubrangeType):
                            self.generate_subrange_test_code(reg, bt)
                        else:
                            self.emit_code("CMP {}, 0".format(reg))
                            self.emit_jump_to_error("JL", "_PASCAL_SUCC_PRED_ERROR")
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_register(node.left_value, reg, comment)
                    elif node.label.name in ("_ROUND_REAL", "_TRUNC_REAL"):
                        comment = "parameter {} for {}()".format(str(parameter_stack[-1].parameter_value),
                                                                 node.label.name[1:6].lower())
                        self.emit_move_to_xmm_register_from_stack("xmm0", parameter_stack[-1].parameter_value, comment)
                        assert node.left_value.pascal_type.size in (4, 8)  # can't round into 1 or 2 bytes
                        destination_register = get_register_slice_by_bytes("RAX", node.left_value.pascal_type.size)
                        if node.label.name == "_ROUND_REAL":
                            # TODO: Possible bug here; CVTSD2SI uses MXCSR rounding mode, which defaults to "nearest"
                            # but can be overridden.
                            instruction = "CVTSD2SI"
                        else:
                            # CVTTSD2SI always truncates towards zero, regardless of MXCSR rounding mode.
                            instruction = "CVTTSD2SI"
                        # TODO - test for overflow here
                        self.emit_code("{} {}, XMM0".format(instruction, destination_register))
                        comment = "assign return value of function to {}".format(node.left_value.name)
                        self.emit_move_to_stack_from_register(node.left_value, destination_register, comment)
                    else:  # pragma: no cover
                        raise ASMGeneratorError(compiler_fail_str(
                            "Invalid System Function: {}".format(node.label.name)))
                elif isinstance(node, TACBinaryNodeWithBoundsCheck):
                    # currently only used for math with structured types where we have pointers
                    assert isinstance(node.result.pascal_type, pascaltypes.PointerType)
                    # only valid binary operation with pointers is addition, when we are accessing
                    # structured types
                    assert node.operator == TACOperator.ADD
                    comment = "{} := {} + {} with bounds check {} to {}"
                    comment = comment.format(node.result.name, node.argument1.name, node.argument2.name,
                                             node.lower_bound,
                                             node.upper_bound)

                    self.emit_move_to_register_from_stack_or_literal("rax", node.argument1, comment)
                    # mov into r11d automatically zero-extends into r11
                    self.emit_move_to_register_from_stack_or_literal("r11d", node.argument2)

                    if isinstance(node.argument2, IntegerLiteral):
                        # bounds-checking should have been done upstream
                        assert node.lower_bound <= int(node.argument2.value) <= node.upper_bound
                    else:
                        # if the value in r11d is less than zero, then we tried to add a negative number, which would be
                        # a subscript out of range.
                        self.emit_code("CMP R11D, {}".format(str(node.lower_bound)))
                        self.emit_jump_to_error("JL", "_PASCAL_ARRAY_INDEX_RANGE_ERROR")

                        # we are only adding to pointers that point to arrays.  Not adding to pointers in the middle
                        # of arrays.  And the addition is always a multiple of the size of the component type.
                        # So, if the number of bytes being added is greater than the size allocated to the pointer,
                        # we have gone over and this would be an index error

                        # TODO - assert someplace that when we're adding we're adding the right multiple.
                        self.emit_code("CMP R11D, {}".format(str(node.upper_bound)))
                        self.emit_jump_to_error("JG", "_PASCAL_ARRAY_INDEX_RANGE_ERROR")

                    self.emit_code("add rax, r11")
                    self.emit_jump_to_error("jo", "_PASCAL_OVERFLOW_ERROR")
                    self.emit_move_to_stack_from_register(node.result, "rax")

                elif isinstance(node, TACBinaryNode):

                    assert isinstance(node.result.pascal_type, pascaltypes.IntegerType) or \
                           isinstance(node.result.pascal_type, pascaltypes.BooleanType) or \
                           isinstance(node.result.pascal_type, pascaltypes.RealType)

                    comment = "{} := {} {} {}".format(node.result.name, node.argument1.name, node.operator,
                                                      node.argument2.name)

                    if isinstance(node.result.pascal_type, pascaltypes.IntegerType):
                        # TODO - handle something other than 4-byte integers
                        if node.operator in (TACOperator.MULTIPLY, TACOperator.ADD, TACOperator.SUBTRACT):
                            if node.operator == TACOperator.MULTIPLY:
                                op = "imul"
                            elif node.operator == TACOperator.ADD:
                                op = "add"
                            else:
                                op = "sub"

                            self.emit_move_to_register_from_stack_or_literal("eax", node.argument1, comment)
                            self.emit_move_to_register_from_stack_or_literal("r11d", node.argument2)
                            self.emit_code("{} eax, r11d".format(op))
                            self.emit_jump_to_error("jo", "_PASCAL_OVERFLOW_ERROR")
                            self.emit_move_to_stack_from_register(node.result, "eax")

                        elif node.operator in (TACOperator.INTEGER_DIV, TACOperator.MOD):
                            self.emit_move_to_register_from_stack_or_literal("eax", node.argument1, comment)
                            self.emit_move_to_register_from_stack_or_literal("r11d", node.argument2)

                            # Error D.45: 6.7.2.2 of ISO Standard requires testing for division by zero at runtime
                            # Error D.46: 6.7.2.2 also says it is an error if the divisor is not positive
                            # 6.7.2.2 also says that the result of the mod operation must be greater than or
                            # equal to zero, and less than the divisor.
                            self.emit_code("test r11d, r11d", "check for division by zero")
                            if node.operator == TACOperator.INTEGER_DIV:
                                self.emit_jump_to_error("je", "_PASCAL_DIVIDE_BY_ZERO_ERROR")
                            else:
                                self.emit_jump_to_error("jle", "_PASCAL_MOD_ERROR")
                            self.emit_code("cdq", "sign extend eax -> edx:eax")
                            self.emit_code("idiv r11d")
                            if node.operator == TACOperator.MOD:
                                self.emit_code("MOV EAX, EDX", "Remainder of INTEGER_DIV is in EDX")
                                positive_mod_label = self.get_next_label()
                                self.emit_code("CMP EAX, 0")
                                self.emit_code("JGE {}".format(positive_mod_label))
                                self.emit_code("ADD EAX, R11D")
                                self.emit_label(positive_mod_label)
                            self.emit_move_to_stack_from_register(node.result, "eax")
                        else:  # pragma: no cover
                            raise ASMGeneratorError("Unrecognized operator: {}".format(node.operator))
                    elif isinstance(node.result.pascal_type, pascaltypes.RealType):
                        if node.operator == TACOperator.MULTIPLY:
                            op = "mulsd"
                        elif node.operator == TACOperator.ADD:
                            op = "addsd"
                        elif node.operator == TACOperator.SUBTRACT:
                            op = "subsd"
                        elif node.operator == TACOperator.DIVIDE:
                            op = "divsd"
                        else:  # pragma: no cover
                            raise ASMGeneratorError("Unrecognized operator: {}".format(node.operator))
                        self.emit_move_to_xmm_register_from_stack("xmm0", node.argument1, comment)
                        self.emit_move_to_xmm_register_from_stack("xmm8", node.argument2, comment)
                        self.emit_code("{} xmm0, xmm8".format(op))
                        self.emit_move_to_stack_from_xmm_register(node.result, "xmm0")

                    else:
                        assert isinstance(node.result.pascal_type, pascaltypes.BooleanType)
                        n1type = node.argument1.pascal_type
                        n2type = node.argument2.pascal_type

                        assert block.symbol_table.are_compatible(n1type.identifier, n2type.identifier, node.argument1,
                                                                 node.argument2)

                        if node.operator in (TACOperator.AND, TACOperator.OR):
                            assert isinstance(n1type, pascaltypes.BooleanType)
                            assert isinstance(n2type, pascaltypes.BooleanType)
                            self.emit_move_to_register_from_stack("al", node.argument1, comment)
                            self.emit_move_to_register_from_stack("r11b", node.argument2)
                            if node.operator == TACOperator.AND:
                                self.emit_code("and al, r11b")
                            else:
                                self.emit_code("or al, r11b")
                            self.emit_move_to_stack_from_register(node.result, "AL")
                        else:
                            if n1type.is_string_type() or isinstance(n1type, pascaltypes.StringLiteralType):
                                self.emit_code("MOV RDI, [{}]".format(node.argument1.memory_address), comment)
                                self.emit_code("MOV RSI, [{}]".format(node.argument2.memory_address))
                                if n1type.is_string_type():
                                    length = n1type.num_items_in_array
                                else:
                                    assert isinstance(node.argument1, ConstantSymbol)
                                    length = len(node.argument1.value)
                                self.emit_code("MOV EDX, {}".format(str(length)))
                                self.emit_code("CALL _PASCAL_STRING_COMPARE")
                                self.emit_code("TEST AL, AL")
                            elif isinstance(n1type, pascaltypes.IntegerType) or \
                                    (isinstance(n1type, pascaltypes.SubrangeType) and
                                     n1type.host_type.size == 4):
                                self.emit_move_to_register_from_stack_or_literal("eax", node.argument1, comment)
                                self.emit_move_to_register_from_stack_or_literal("r11d", node.argument2)
                                self.emit_code("cmp eax, r11d")
                            elif isinstance(n1type, pascaltypes.BooleanType) or \
                                    isinstance(n1type, pascaltypes.CharacterType) or \
                                    isinstance(n1type, pascaltypes.EnumeratedType) or \
                                    (isinstance(n1type, pascaltypes.SubrangeType) and
                                     n1type.host_type.size == 1):
                                self.emit_move_to_register_from_stack("al", node.argument1, comment)
                                self.emit_move_to_register_from_stack("r11b", node.argument2)
                                self.emit_code("cmp al, r11b")
                            else:  # has to be real; we errored above if any other type
                                assert isinstance(n1type, pascaltypes.RealType)
                                self.emit_move_to_xmm_register_from_stack("xmm0", node.argument1)
                                self.emit_move_to_xmm_register_from_stack("xmm8", node.argument2)
                                self.emit_code("ucomisd xmm0, xmm8")

                            if isinstance(n1type, pascaltypes.BooleanType) or \
                                    isinstance(n1type, pascaltypes.IntegerType) or \
                                    is_integer_or_boolean_subrange_type(n1type) or \
                                    n1type.is_string_type() or \
                                    isinstance(n1type, pascaltypes.StringLiteralType):

                                # Boolean and Integer share same jump instructions, and strings
                                # are set up to do an integer comparison by this point
                                if node.operator == TACOperator.EQUALS:
                                    jump_instruction = "JE"
                                elif node.operator == TACOperator.NOT_EQUAL:
                                    jump_instruction = "JNE"
                                elif node.operator == TACOperator.GREATER:
                                    jump_instruction = "JG"
                                elif node.operator == TACOperator.GREATER_EQUAL:
                                    jump_instruction = "JGE"
                                elif node.operator == TACOperator.LESS:
                                    jump_instruction = "JL"
                                elif node.operator == TACOperator.LESS_EQUAL:
                                    jump_instruction = "JLE"
                                else:  # pragma: no cover
                                    raise ASMGeneratorError("Invalid Relational Operator {}".format(node.operator))
                            else:
                                assert isinstance(n1type, pascaltypes.RealType) or \
                                       isinstance(n1type, pascaltypes.CharacterType) or \
                                       isinstance(n1type, pascaltypes.EnumeratedType) or \
                                       isinstance(n1type, pascaltypes.SubrangeType)
                                if node.operator == TACOperator.EQUALS:
                                    jump_instruction = "JE"
                                elif node.operator == TACOperator.NOT_EQUAL:
                                    jump_instruction = "JNE"
                                elif node.operator == TACOperator.GREATER:
                                    jump_instruction = "JA"
                                elif node.operator == TACOperator.GREATER_EQUAL:
                                    jump_instruction = "JAE"
                                elif node.operator == TACOperator.LESS:
                                    jump_instruction = "JB"
                                elif node.operator == TACOperator.LESS_EQUAL:
                                    jump_instruction = "JBE"
                                else:  # pragma: no cover
                                    raise ASMGeneratorError("Invalid Relational Operator {}".format(node.operator))

                            true_label = self.get_next_label()
                            done_label = self.get_next_label()
                            self.emit_code("{} {}".format(jump_instruction, true_label))
                            self.emit_code("mov al, 0")
                            self.emit_code("jmp {}".format(done_label))
                            self.emit_label(true_label)
                            self.emit_code("mov al, 1")
                            self.emit_label(done_label)
                            self.emit_move_to_stack_from_register(node.result, "al")
                else:  # pragma: no cover
                    raise ASMGeneratorError("Unknown TAC node type: {}".format(type(node)))

            if block.is_main:
                # deallocate global arrays
                # TODO: refactor this loop to be something like "get global array symbols" or something
                for symbol_name in self.tac_generator.global_symbol_table.symbols.keys():
                    symbol = self.tac_generator.global_symbol_table.fetch(symbol_name)
                    if isinstance(symbol, Symbol) and isinstance(symbol.pascal_type, pascaltypes.ArrayType):
                        self.emit_code("mov rdi, [{}]".format(symbol.memory_address),
                                       "Free memory for global array {}".format(symbol_name))
                        self.used_dispose = True
                        self.emit_code("call _PASCAL_DISPOSE_MEMORY")
            else:
                # deallocate local arrays
                for symbol_name in block.symbol_table.symbols.keys():
                    if block.parameter_list.fetch(symbol_name) is None:
                        local_symbol = block.symbol_table.symbols[symbol_name]
                        if isinstance(local_symbol, Symbol) and not isinstance(local_symbol,
                                                                               FunctionResultVariableSymbol):
                            if isinstance(local_symbol.pascal_type, pascaltypes.ArrayType):
                                self.emit_code("mov rdi, [{}]".format(local_symbol.memory_address),
                                               "Free memory for local array {}".format(symbol_name))
                                self.used_dispose = True
                                self.emit_code("call _PASCAL_DISPOSE_MEMORY")

            if total_storage_needed_bytes > 0 or block.is_main:
                self.emit_code("MOV RSP, RBP", "restore stack pointer")
                self.emit_code("POP RBP")

            if not block.is_main:
                self.emit_code("RET")

    def generate_helper_function_code(self):
        if self.used_calloc:
            self.emit_label("_PASCAL_ALLOCATE_MEMORY")
            self.emit_comment("takes a number of members (RDI) and a size (RSI)")
            self.emit_comment("returns pointer to memory in RAX.")
            # just a passthrough for CALLOC
            # yes, calloc() initializes memory and Pascal is not supposed to do so, but calloc() is safer
            # in that it tests for an overflow when you multiply number of members * size whereas malloc() does not.
            self.emit_code("call calloc wrt ..plt")
            self.emit_code("test rax, rax")
            self.emit_jump_to_error("jle", "_PASCAL_CALLOC_ERROR")
            self.emit_code("ret")
        if self.used_dispose:
            self.emit_label("_PASCAL_DISPOSE_MEMORY")
            self.emit_comment("takes a pointer to memory (RDI)")
            # just a passthrough for FREE
            self.emit_code("call free wrt ..plt")
            self.emit_code("test rax, rax")
            self.emit_jump_to_error("jl", "_PASCAL_DISPOSE_ERROR")
            self.emit_code("ret")

    def generate_error_handling_code(self):
        for runtime_error in self.runtime_errors:
            if runtime_error.is_used:
                self.emit_label(runtime_error.label)
                self.emit_code("lea rsi, [rel _pascal_error_{}]".format(str(self.runtime_errors.index(runtime_error))))
                self.emit_code("mov rdx, {}".format(len(runtime_error.error_string)))
                self.emit_code("jmp _PASCAL_PRINT_ERROR")

        self.emit_label("_PASCAL_PRINT_ERROR")
        self.emit_comment("required: pointer to error message in rsi, length of message in rdx")
        self.emit_code("PUSH RSI")
        self.emit_code("PUSH RDX")  # we pushed 16-bytes so stack is still 16-byte aligned
        self.emit_code("XOR RDI, RDI", "need to flush any buffered output before printing the error")
        self.emit_code("CALL fflush wrt ..plt")
        self.emit_code("POP RDX")
        self.emit_code("POP RSI")
        # uses syscalls here because we don't know if "output" was defined
        self.emit_code("mov rax, 1")
        self.emit_code("mov rdi, 1", "1 = stdout")
        self.emit_code("syscall")
        self.emit_code("jmp _PASCAL_EXIT")

    def generate_program_termination_code(self):
        self.emit_comment("exit program")
        self.emit_label("_PASCAL_EXIT")
        self.emit_comment("Need to flush the stdout buffer, as exiting does not do it.")
        self.emit_code("XOR RDI, RDI")
        self.emit_code("CALL fflush wrt ..plt")
        self.emit_code("MOV EAX, 60")
        self.emit_code("SYSCALL")

    def generate_text_section(self):
        self.emit_section("text")
        self.emit_code("global main")
        self.generate_code()
        self.emit_code("JMP _PASCAL_EXIT")
        self.generate_helper_function_code()
        self.generate_error_handling_code()
        self.generate_program_termination_code()

    def generate_gnu_stack_section(self):
        # notify the linker that we do not need an executable stack
        self.emit_section("note.GNU-stack noalloc noexec nowrite progbits")

    def generate_bss_section(self):
        if len(self.tac_generator.global_symbol_table.symbols.keys()) > 0:
            self.emit_section("bss")
            global_variable_label_sequence = 0
            for symbol_name in self.tac_generator.global_symbol_table.symbols.keys():
                symbol = self.tac_generator.global_symbol_table.fetch(symbol_name)
                if isinstance(symbol, Symbol) and not isinstance(symbol, ActivationSymbol):
                    if isinstance(symbol, ProgramParameterSymbol):
                        if symbol.name not in ("input", "output"):
                            label2 = "_global_variable_{}_file_name_pointer".format(symbol.name)
                            symbol.filename_memory_address = "rel {}".format(label2)
                            self.emit_code("{} resb {}".format(label2, 8), "holds pointer to command-line arg")
                        label = "_global_variable_{}".format(symbol.name)
                    else:
                        label = "_global_variable_{}".format(str(global_variable_label_sequence))
                        global_variable_label_sequence += 1
                    symbol.memory_address = "rel {}".format(label)
                    if isinstance(symbol.pascal_type, pascaltypes.ArrayType):
                        self.emit_code("{} resb 8".format(label),
                                       "address for global array variable {}".format(symbol_name))
                    else:
                        self.emit_code("{} resb {}".format(label, symbol.pascal_type.size),
                                       "global variable {}".format(symbol_name))

    def generate(self, object_file_name, executable_file_name):
        self.generate_extern_references()
        self.generate_gnu_stack_section()
        self.generate_bss_section()
        self.generate_data_section()
        self.generate_text_section()
        self.assembly_file.close()
        os.system("nasm -f elf64 -F dwarf -g -o compiler2_system_io.o compiler2_system_io.asm")
        os.system("nasm -f elf64 -F dwarf -g -o compiler2_stringcompare.o compiler2_stringcompare.asm")
        os.system("nasm -f elf64 -F dwarf -g -o {} {}".format(object_file_name, self.assembly_file_name))
        os.system("gcc {} -o {} compiler2_system_io.o compiler2_stringcompare.o".format(object_file_name,
                                                                                        executable_file_name))
