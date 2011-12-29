import re
import os

class Template(object):
    """
    akpytemp
    ========
    A simple and feature-rich general purpose templating utility

    Basic test cases:
    >>> def world():
    ...     return 'world'
    >>> template = Template('Hello {# world() #}, templates{# exclaim #}')
    >>> template.render(locals(), exclaim='!')
    'Hello world, templates!'
    >>> Template('{# def f(): return 42 #}The answer is: {# f() #}').render()
    'The answer is: 42'

    Some control logic test cases:
    >>> Template('{% for i in xrange(10) %}{# 2 ** i #}, {% end %}').render()
    '1, 2, 4, 8, 16, 32, 64, 128, 256, 512, '
    >>> Template(
    ...         '2 + 4 {% if 2 + 4 == 6 %}=={% else %}!={% end %} 6'
    ...         ).render()
    '2 + 4 == 6'

    Nested logic:
    >>> template = Template(
    ...         '{% for i in [0, 1] %}{% if i %}{# i #}{% end %}{% end %}')
    >>> template.render()
    '1'

    Includeing templates:
    >>> Template(path='test/include_test.template').render()
    'Hello world!'

    Other stuff:
    >>> template = Template('Hello {# __emit__(world) #}!')
    >>> template.render(world='world')
    'Hello world!'
    """
    def __init__(self, template=None, path=None):
        self._path = path if path else '.'
        if not template:
            self._template = self._read_file(path)
        else:
            self._template = template
        self._delimiters = {
                'left_expr': r'{#',        'right_expr': r'#}',
                'left_for':  r'{%\s+for',  'right_for':  r'%}',
                'left_if':   r'{%\s+if',   'right_if':   r'%}',
                'left_else': r'{%\s+else', 'right_else': r'%}',
                'left_end':  r'{%\s+end',  'right_end':  r'%}', }
        self._globals = None
        self._locals_init = {
                'include': self._include,
                '__render__': self._render_r,
                '__emit__': self._emit, }
        self._locals = dict(self._locals_init)
        self._rendered = None
        self._emit_enable = True

    def _read_file(self, path):
        string = ''.join(open(path).readlines())
        if string.endswith('\n'):
            string = string[:-1]
        return string

    def _lex(self, template):
        """
        Perform lexical analysis on the template string
        Return a list of tuples, each containing the value
        and its designated token
        """
        def matching_delimiter_re(delimiter_re):
            key = key_for_value(self._delimiter_re, delimiter_re)
            pair = ['left', 'right']
            for idx, val in enumerate(pair):
                if val in key:
                    new_key = key.replace(pair[idx], pair[1 - idx])
            return self._delimiter_re[new_key]
        # construct regexes
        self._delimiter_re = {}
        for key, val in self._delimiters.iteritems():
            self._delimiter_re[key] = re.compile('(' + val + ')')
        # split template
        lexed_template = [template]
        for regex in self._delimiter_re.itervalues():
            lexed_template = chop(lexed_template, regex)
        # assign tokens
        token_re = re.compile('.*_(.*)')
        lexed = []
        idx = 0
        lexed_template_size = len(lexed_template)
        while idx < lexed_template_size:
            is_code = False
            lexed_str = lexed_template[idx]
            ldlim_res = re_lookup_val(self._delimiter_re, 'left.*')
            for ldlim_key, ldlim_re in ldlim_res:
                # search for left delimiters
                if not ldlim_re.match(lexed_str):
                    continue
                # found and expect code tokens
                is_code = True
                # left delimiter consistency checks
                error_str = None
                rdlim_re = matching_delimiter_re(ldlim_re)
                if not rdlim_re.match(lexed_template[idx + 2]):
                    error_str = ''.join(lexed_template[idx:(idx + 2)])
                if error_str:
                    raise SyntaxError('\'%s\'\nCode block is not terminated'
                            % error_str)
                # tokenise
                token_re_results = token_re.search(ldlim_key)
                if token_re_results.groups < 1:
                    raise Exception('\'%s\'\nInvalid lexer structure'
                            % ldlim_key)
                lexed.append((lexed_template[idx + 1],
                        token_re_results.group(1)))
                idx += 3
            # right delimiter consistency checks
            rdlim_res = re_lookup_val(self._delimiter_re, 'right.*')
            for _, rdlim_re in rdlim_res:
                if not rdlim_re.match(lexed_str):
                    continue
                if idx > 0:
                    error_str = lexed_template[idx - 1] + lexed_str
                else:
                    error_str = lexed_str
                raise SyntaxError('\'%s\'\nNo code block to terminate'
                        % error_str)
            if not is_code:
                if lexed_str:
                    lexed.append((lexed_str, 'text'))
                idx += 1
        return lexed

    def _clear(self):
        self._rendered = ''

    def _emit(self, rendered_text):
        if not self._emit_enable:
            return
        if rendered_text:
            self._rendered += rendered_text

    def _include(self, path):
        folder = os.path.split(self._path)[0]
        include_file = os.path.join(folder, path)
        include_template = Template(path=include_file)
        include_result = include_template.render(namespace=self._globals)
        include_globals = include_template._globals
        self._emit(include_result)
        self._globals.update(include_globals)

    def _render_r(self, lexed_template):
        """
        Recursive render calls
        """
        def enclosing_template(idx, token, lexed_template):
            """
            Search for matching 'else' or 'end' statement
            """
            depth = 1
            render_template = []
            for end_idx in xrange(idx + 1, len(lexed_template)):
                (end_str, end_token) = lexed_template[end_idx]
                if 'for' == end_token or 'if' == end_token:
                    depth += 1
                elif 'end' == end_token:
                    depth -= 1
                if depth == 0 or (depth == 1 and 'else' == end_token):
                    return end_idx, end_token, render_template
                render_template.append((end_str, end_token))
            return 0, None, None
        def tail_colon(text):
            new_text = text.rstrip()
            if not new_text.endswith(':'):
                new_text += ':'
            return new_text
        idx = 0
        while idx < len(lexed_template):
            (lexed_str, token) = lexed_template[idx]
            eval_result = None
            if 'text' == token:
                self._emit(lexed_str)
                idx += 1
            elif 'expr' == token:
                lexed_str = code_gobble(lexed_str)
                eval_result = self._eval(lexed_str)
                idx += 1
            elif 'for' == token or 'if' == token:
                end_idx, end_token, if_template= enclosing_template(
                        idx, token, lexed_template)
                else_template = None
                if end_token == 'else':
                    end_idx, end_token, else_template = enclosing_template(
                            end_idx, end_token, lexed_template)
                if end_token != 'end':
                    raise SyntaxError(
                            '%s, Block statement is not terminated'
                            % lexed_str)
                eval_str = tail_colon(token.lstrip() + ' ' + lexed_str)
                eval_str += '\n    '
                eval_str += '__render__(%s)' % if_template
                if else_template:
                    eval_str += '\nelse:\n    '
                    eval_str += '__render_r__(%s)' % else_template
                eval_result = self._eval(eval_str)
                idx = end_idx + 1
            else:
                raise SyntaxError('\'%s\'\nUnexpected token, source \'%s\''
                        % (token, lexed_str))
            if not eval_result is None:
                self._emit(str(eval_result))
        return self._rendered

    def render(self, namespace=None, **kwargs):
        """
        Render the template
        """
        if not namespace:
            namespace = {}
        if kwargs:
            namespace.update(kwargs)
        self._globals = namespace
        self._clear()
        lexed_template = self._lex(self._template)
        return self._render_r(lexed_template)

    def _eval(self, block):
        """
        Run a block of code, return the return value from the code
        """
        if not self._globals:
            self._globals = {}
        # make sure globals has the correct method calls
        # for the instance
        self._globals.update(self._locals_init)
        result = None
        try:
            result = eval(block, self._globals, self._locals)
        except SyntaxError:
            exec block in self._globals, self._locals
        # FIXME: Python can only make imports local
        # if executed in local scope
        # This hack would eventually in some cases
        # result in namespace collision problem
        self._globals.update(self._locals)
        self._locals.clear()
        return result

def key_for_value(dictionary, value):
    """
    Find key for a specified value in a dictionary
    """
    for key, val in dictionary.iteritems():
        if val == value:
            return key

def re_lookup_val(dictionary, regex):
    """
    Lookup values by using a regex to match keys in dictionary
    """
    key_re = re.compile(regex)
    for key, val in dictionary.iteritems():
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

def code_gobble(code, gobble_count=-1):
    ws_re = re.compile('^(\s+)')
    new_code_list = []
    for line in code.splitlines(0):
        if not line.strip():
            continue
        line = line.replace('\t', '    ')
        if gobble_count < 0:
            ws_match = ws_re.match(line)
            if not ws_match:
                return code
            else:
                gobble_ws = ws_match.group(1)
                gobble_count = len(gobble_ws)
        if gobble_ws != line[:gobble_count]:
            raise IndentationError('%s for gobble count %d'
                    % (line, gobble_count))
        new_code_list.append(line[gobble_count:])
    return '\n'.join(new_code_list)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
