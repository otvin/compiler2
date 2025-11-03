from enum import Enum
from lexer import Token

# source: https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
# usage: print one of the formats and then print ENDC
ANSI_OKBLUE = '\033[94m'
ANSI_OKCYAN = '\033[96m'
ANSI_OKGREEN = '\033[92m'
ANSI_WARNINGYELLOW = '\033[93m'
ANSI_FAILRED = '\033[91m'
ANSI_BOLD = '\033[1m'
ANSI_UNDERLINE = '\033[4m'

ANSI_ENDC = '\033[0m'

class ErrLevel(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2

def levstr(errlevel):
    assert(errlevel in [ErrLevel.INFO, ErrLevel.WARNING, ErrLevel.ERROR])
    if errlevel == ErrLevel.INFO:
        ret = '{}{}note:{}'.format(ANSI_BOLD, ANSI_OKCYAN, ANSI_ENDC)
    elif errlevel == ErrLevel.WARNING:
        ret = '{}{}warning:{}'.format(ANSI_BOLD, ANSI_WARNINGYELLOW,ANSI_ENDC)
    else:
        ret = '{}{}error:{}'.format(ANSI_BOLD, ANSI_FAILRED, ANSI_ENDC)
    return ret

def compiler_errstr(errstr, errtok = None):
    if errtok is not None:
        assert(isinstance(errtok, Token))
    prolog = ""
    curlinestr = ""
    if errtok is not None:
        prolog = errtok.location.getprolog() + " "
        curlinestr = '{:>6} | {}\n\t'.format(errtok.location.line, errtok.location.curlinestr)
    ret = '{}{}{}{} {}\n{}'.format(ANSI_BOLD, prolog, ANSI_ENDC, levstr(ErrLevel.ERROR), errstr, curlinestr)
    return ret
