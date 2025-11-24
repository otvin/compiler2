from enum import Enum
from lexer import Token
from filelocation import FileLocation

# source: https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
# usage: print one of the formats and then print ENDC
ANSI_BLUE = '\033[94m'
ANSI_CYAN = '\033[96m'
ANSI_GREEN = '\033[92m'
ANSI_YELLOW = '\033[93m'
ANSI_RED = '\033[91m'
ANSI_RED_ON_BLUE = '\033[91;104m'
ANSI_BOLD = '\033[1m'
ANSI_UNDERLINE = '\033[4m'

ANSI_ENDC = '\033[0m'


class ErrorLevel(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    FAIL = 3


def error_level_format_str(error_level):
    assert error_level in [ErrorLevel.INFO, ErrorLevel.WARNING, ErrorLevel.ERROR, ErrorLevel.FAIL]
    if error_level == ErrorLevel.INFO:
        ret = '{}{}note:{}'.format(ANSI_BOLD, ANSI_CYAN, ANSI_ENDC)
    elif error_level == ErrorLevel.WARNING:
        ret = '{}{}warning:{}'.format(ANSI_BOLD, ANSI_YELLOW, ANSI_ENDC)
    elif error_level == ErrorLevel.ERROR:
        ret = '{}{}error:{}'.format(ANSI_BOLD, ANSI_RED, ANSI_ENDC)
    else:  # pragma: no cover
        ret = '{}{}!!FAIL:{}'.format(ANSI_BOLD, ANSI_RED_ON_BLUE, ANSI_ENDC)
    return ret


def compiler_notify_str(notify_str, error_level, token=None, location=None):
    # if token is not defined, then will look at location.  If both token and location are defined,
    # location is ignored.

    if token is not None:
        assert (isinstance(token, Token))
    if location is not None:
        assert (isinstance(location, FileLocation))
    prolog = ""
    current_line_str = ""
    if token is not None:
        location = token.location
    if location is not None:
        prolog = location.getprolog() + " "
        current_line_str = '{:>6} | {}\n'.format(location.line, location.curlinestr)
    ret = '{}{}{}{} {}\n{}'.format(ANSI_BOLD, prolog, ANSI_ENDC, error_level_format_str(error_level), notify_str,
                                   current_line_str)
    return ret


def compiler_warn_str(warn_str, token=None, location=None):
    return compiler_notify_str(warn_str, ErrorLevel.WARNING, token, location)


def compiler_error_str(error_str, token=None, location=None):
    return compiler_notify_str(error_str, ErrorLevel.ERROR, token, location)


def compiler_fail_str(fail_str):
    return '{}{}'.format(error_level_format_str(ErrorLevel.FAIL), fail_str)
