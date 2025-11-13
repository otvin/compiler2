from enum import Enum
from lexer import Token
from filelocation import FileLocation

# source: https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
# usage: print one of the formats and then print ENDC
ANSI_OKBLUE = '\033[94m'
ANSI_OKCYAN = '\033[96m'
ANSI_OKGREEN = '\033[92m'
ANSI_WARNINGYELLOW = '\033[93m'
ANSI_ERRORRED = '\033[91m'
ANSI_FAIL = '\033[91;104m'
ANSI_BOLD = '\033[1m'
ANSI_UNDERLINE = '\033[4m'

ANSI_ENDC = '\033[0m'

class ErrLevel(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    FAIL = 3

def levstr(errlevel):
    assert(errlevel in [ErrLevel.INFO, ErrLevel.WARNING, ErrLevel.ERROR, ErrLevel.FAIL])
    if errlevel == ErrLevel.INFO:
        ret = '{}{}note:{}'.format(ANSI_BOLD, ANSI_OKCYAN, ANSI_ENDC)
    elif errlevel == ErrLevel.WARNING:
        ret = '{}{}warning:{}'.format(ANSI_BOLD, ANSI_WARNINGYELLOW,ANSI_ENDC)
    elif errlevel == ErrLevel.ERROR:
        ret = '{}{}error:{}'.format(ANSI_BOLD, ANSI_ERRORRED, ANSI_ENDC)
    else:
        ret = '{}{}!!FAIL:{}'.format(ANSI_BOLD, ANSI_FAIL, ANSI_ENDC)
    return ret

def compiler_notifystr(errstr, errlevel, errtok = None, errloc = None):
    # if errtok is not defined, then will look at location in errloc.  If both errtok and errloc are defined
    # errloc is ignored.

    if errtok is not None:
        assert (isinstance(errtok, Token))
    if errloc is not None:
        assert (isinstance(errloc, FileLocation))
    prolog = ""
    curlinestr = ""
    if errtok is not None:
        errloc = errtok.location
    if errloc is not None:
        prolog = errloc.getprolog() + " "
        curlinestr = '{:>6} | {}\n'.format(errloc.line, errloc.curlinestr)
    ret = '{}{}{}{} {}\n{}'.format(ANSI_BOLD, prolog, ANSI_ENDC, levstr(errlevel), errstr, curlinestr)
    return ret

def compiler_warnstr(errstr, errtok = None, errloc = None):
    return compiler_notifystr(errstr, ErrLevel.WARNING, errtok, errloc)

def compiler_errstr(errstr, errtok = None, errloc = None):
    return compiler_notifystr(errstr, ErrLevel.ERROR, errtok, errloc)

def compiler_failstr(errstr):
    return '{}{}'.format(levstr(ErrLevel.FAIL), errstr)
