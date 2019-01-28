class FileLocation:
    def __init__(self, filename, line, column):
        self.filename = filename
        self.line = line
        self.column = column

    def __str__(self):
        return 'file:{0:<15} line:{1:<5} column:{2:<3}\n'.format(self.filename, self.line, self.column)
