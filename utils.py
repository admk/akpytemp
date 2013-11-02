import re
import sys


def key_for_value(dictionary, value):
    """
    Find key for a specified value in a dictionary
    """
    for key, val in dictionary.items():
        if val == value:
            return key


def re_lookup_val(dictionary, regex):
    """
    Lookup values by using a regex to match keys in dictionary
    """
    key_re = re.compile(regex)
    for key, val in dictionary.items():
        if key_re.match(key):
            yield key, val
    return


def chop(token_list, regex):
    """
    Chop a list of strings with a regex
    Think of it as a regex.split with list support
    """
    new_token_list = []
    for token in token_list:
        for new_token in regex.split(token):
            if new_token:
                new_token_list.append(new_token)
    return new_token_list


def code_gobble(code, gobble_count=None, eat_empty_lines=False):
    ws_re = re.compile('^(\s+)')
    new_code_list = []
    for line in code.splitlines(0):
        if not line.strip():
            if not eat_empty_lines:
                new_code_list.append('')
            continue
        line = line.replace('\t', '    ')
        if gobble_count is None:
            ws_match = ws_re.match(line)
            if not ws_match:
                return code
            else:
                gobble_ws = ws_match.group(1)
                gobble_count = len(gobble_ws)
        if gobble_ws != line[:gobble_count]:
            raise IndentationError(
                '%s for gobble count %d' % (line, gobble_count))
        new_code_list.append(line[gobble_count:])
    return '\n'.join(new_code_list)


if sys.hexversion > 0x03000000:
    def _exec(source, globals=None, locals=None):
        exec(source, globals, locals)

    def _eval(source, globals=None, locals=None):
        return eval(source, globals, locals)
else:
    eval(compile(code_gobble(
        """
        def _exec(source, globals=None, locals=None):
            exec source in globals, locals
        """), "<exec_function>", "exec"))

    def _eval(source, globals=None, locals=None):
        return eval(source, globals, locals)
