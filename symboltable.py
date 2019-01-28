class SymbolException(Exception):
    pass


class SymbolRedefinedException(SymbolException):
    pass


class Symbol:
    def __init__(self, name, location, pascaltype):
        self.name = name.lower()
        self.location = location
        self.pascaltype = pascaltype


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
