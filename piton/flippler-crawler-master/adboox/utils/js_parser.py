from pyparsing import Suppress, Regex, Optional, Group, Literal, Word, Forward
from pyparsing import alphas, alphanums, delimitedList, quotedString, cStyleComment


LBR, RBR, LCUR, RCUR = [Suppress(x) for x in '[]{}']
IDENTIFIER = Word(alphas + '_', alphanums + '_')

INT_DECIMAL = Regex('([+-]?(([1-9][0-9]*)|0+))')
INT_DECIMAL.setParseAction(lambda x: int(x[0]))

INT_OCTAL = Regex('(0[0-7]*)')
INT_OCTAL.setParseAction(lambda x: int(x[0], 8))

INT_HEXADECIMAL = Regex('(0[xX][0-9a-fA-F]*)')
INT_HEXADECIMAL.setParseAction(lambda x: int(x[0], 16))

INTEGER = INT_HEXADECIMAL | INT_OCTAL | INT_DECIMAL

FLOAT = Regex(r'[+-]?(((\d+\.\d*)|(\d*\.\d+))([eE][-+]?\d+)?)|(\d*[eE][+-]?\d+)')
FLOAT.setParseAction(lambda x: float(x[0]))

QUOTED_STRING = quotedString
QUOTED_STRING.setParseAction(lambda x: x[0][1:-1])

TRUE = Literal('true')
TRUE.setParseAction(lambda _: True)

FALSE = Literal('false')
FALSE.setParseAction(lambda _: False)

BOOLEAN = TRUE | FALSE

JS_VALUE = Forward()

DICT_ITEM = Group((IDENTIFIER | QUOTED_STRING) + Literal(':').suppress() + JS_VALUE)

DICT = LCUR + Optional(delimitedList(DICT_ITEM)) + RCUR
DICT.setParseAction(lambda x: dict(x.asList()))

LIST = LBR + delimitedList(Optional(JS_VALUE)) + RBR
LIST.setParseAction(lambda x: [x.asList()])

JS_VALUE << (DICT | LIST | QUOTED_STRING | FLOAT | INTEGER | BOOLEAN)

ASSIGNMENT = Group(IDENTIFIER.setResultsName('variable') + Literal('=').suppress() + JS_VALUE.setResultsName('value'))

JS_VAR = Literal('var').suppress() + delimitedList(ASSIGNMENT) + Literal(';').suppress()
JS_VAR.ignore(cStyleComment)


def parse_variables(text):
    ret = {}
    for tokens in JS_VAR.searchString(text):
        for token in tokens:
            ret[token.variable] = token.value
    return ret

def remove_commented_out_jscode(text):
    """
    Removes the commented out js code block from the given text.
    Example:
        'var x = 12; /* var x = 15; */ var y = 15;' becomes 'var x = 12;  var y = 15;'
    """
    cleaned = ''
    stack = []
    buffer = []
    chars = ['/', '*']
    open_seq = ''.join(chars)
    close_seq = ''.join(reversed(chars))
    for c in text:
        if buffer:
            in_buffer = buffer.pop()
            if in_buffer + c == open_seq:
                stack.append(in_buffer)
            elif in_buffer + c == close_seq:
                stack.pop()
            else:
                cleaned += in_buffer
        elif c in chars:
            buffer.append(c)
        if not (stack or buffer):
            cleaned += c
    return cleaned

