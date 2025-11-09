class FileLocation:
    def __init__(self, filename, line, column, curlinestr):
        self.filename = filename
        self.line = line
        self.column = column
        self.curlinestr = curlinestr

    def getprolog(self):
        return '{}:{}:{}:'.format(self.filename, self.line, self.column)

    def __str__(self): # pragma: no cover
        return 'file:{0:<15} line:{1:<5} column:{2:<3}'.format(self.filename, self.line, self.column)
