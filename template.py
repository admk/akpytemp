import re
import os
import sys
import inspect

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
    >>> template = Template('Hello {# emit(world) #}!')
    >>> template.render(world='world')
    'Hello world!'
    >>> Template('1{# set_emit_enable(False) #}2').render()
    '1'
    """
    def __init__(self, template=None, path=None):
        """
        Constructor
        template: a string containing a template
        path: the path to the template file, also used to determine
        template file search path
        """
        # initialise template
        self._path = path
        splited_path = os.path.split(path)
        self._name = splited_path[1]
        self._dir = os.path.abspath(splited_path[0])
        if not template:
            f = open(path)
            template = f.read()
            f.close()
            if template.endswith('\n'):
                template = template[:-1]
            self._template = template
        else:
            self._template = template
        # delimiter tokens
        self._delimiters = {
                'left_expr': r'{#',        'right_expr': r'#}',
                'left_for':  r'{%\s+for',  'right_for':  r'%}',
                'left_if':   r'{%\s+if',   'right_if':   r'%}',
                'left_elif': r'{%\s+elif', 'right_elif': r'%}',
                'left_else': r'{%\s+else', 'right_else': r'%}',
                'left_end':  r'{%\s+end',  'right_end':  r'%}', }
        # rendering
        self._rendered = None
        self._emit_enable = True
        self._eat_whitespaces = False
        self._eat_blanklines = False
        # namespaces
        self._globals = None
        self._locals_init = {
                '__set__': self._set,
                '__get__': self._get,
                '__render__': self._render_r, }
        def append_to_template(method):
            self._locals_init[method[0]] = getattr(self, method[0])
        methods = inspect.getmembers(Template, predicate=inspect.ismethod)
        for method in methods:
            if method[0].startswith('_'):
                continue
            append_to_template(method)
        self._locals = dict(self._locals_init)

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

    def clear(self):
        """
        Clear all rendered content
        """
        self._rendered = ''

    _bl_re = re.compile(r'^\s*\n$')
    _ws_re = re.compile(r'^\s*$')
    def emit(self, rendered_text):
        """
        Render directly to output
        """
        if not self._emit_enable:
            return
        if not rendered_text:
            return
        if self._eat_blanklines:
            if self._bl_re.match(rendered_text):
                return
        if self._eat_whitespaces:
            splited = rendered_text.splitlines(0)
            for idx, text in enumerate(splited):
                if not self._ws_re.match(text):
                    splited[idx] = text.lstrip()
            rendered_text = '\n'.join(splited)
        self._rendered += rendered_text

    def _set(self, key, val):
        """
        Private setter
        """
        self.__dict__[key] = val

    def _get(self, key):
        """
        Private getter
        """
        return self.__dict__[key]

    def include(self, path, emit=True):
        """
        Include and render template file from a template
        """
        include_file = os.path.join(self._dir, path)
        include_template = Template(path=include_file)
        include_result = include_template.render(namespace=self._globals)
        include_globals = include_template._globals
        self._globals.update(include_globals)
        if not emit:
            return
        self.emit(include_result)

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
                if depth == 0 or (depth == 1 and (
                        'else' == end_token or
                        'elif' == end_token)):
                    return end_idx, end_token, render_template
                render_template.append((end_str, end_token))
            return 0, None, None
        idx = 0
        while idx < len(lexed_template):
            (lexed_str, token) = lexed_template[idx]
            eval_result = None
            if 'text' == token:
                self.emit(lexed_str)
                idx += 1
            elif 'expr' == token:
                lexed_str = code_gobble(lexed_str)
                eval_result = self._eval(lexed_str)
                idx += 1
            elif 'for' == token or 'if' == token:
                def code_gen(token, lexed_str, template):
                    def tail_colon(text):
                        new_text = text.rstrip()
                        if not new_text.endswith(':'):
                            new_text += ':'
                        return new_text
                    eval_str = tail_colon(token.lstrip() + ' ' + lexed_str)
                    eval_str += '\n    '
                    eval_str += '__render__(%s)\n' % template
                    return eval_str
                end_idx, end_token, if_template= enclosing_template(
                        idx, token, lexed_template)
                eval_str = code_gen(token, lexed_str, if_template)
                while 'elif' == end_token:
                    prev_idx = end_idx
                    end_idx, end_token, elif_template = enclosing_template(
                            end_idx, end_token, lexed_template)
                    eval_str += code_gen(
                            'elif', lexed_template[prev_idx][0], elif_template)
                if end_token == 'else':
                    end_idx, end_token, else_template = enclosing_template(
                            end_idx, end_token, lexed_template)
                    eval_str += code_gen('else', '', else_template)
                if end_token != 'end':
                    raise SyntaxError(
                            '%s, Block statement is not terminated'
                            % lexed_str)
                eval_result = self._eval(eval_str)
                idx = end_idx + 1
            else:
                raise SyntaxError('\'%s\'\nUnexpected token, source \'%s\''
                        % (token, lexed_str))
            if not eval_result is None:
                self.emit(str(eval_result))
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
        self.clear()
        lexed_template = self._lex(self._template)
        sys.path.append(self._dir)
        result = self._render_r(lexed_template)
        sys.path.remove(self._dir)
        return result

    def save(self, path, **kwargs):
        if os.path.isdir(path):
            path = os.path.join(path, self._name)
        if not self._rendered:
            self.render(**kwargs)
        try:
            f = open(path, 'w')
        except IOError:
            os.makedirs(os.path.split(path)[0])
            f = open(path, 'w')
        f.write(self._rendered)
        f.close()

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

    def emit_enable(self):
        return self._emit_enable

    def set_emit_enable(self, enable):
        self._emit_enable = enable

    def eat_whitespaces(self):
        return self._eat_whitespaces

    def set_eat_whitespaces(self, eat):
        self._eat_whitespaces = eat

    def eat_blanklines(self):
        return self._eat_blanklines

    def set_eat_blanklines(self, eat):
        self._eat_blanklines = eat

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
