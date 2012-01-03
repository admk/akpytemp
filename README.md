akpytemp - A Simple but Awesome General Purpose Templating Utility
==================================================================

Installation
------------
* Clone from Github

        git clone git@github.com:admk/akpytemp.git akpytemp

* Install by executing

        cd akpytemp
        python setup.py build
        python setup.py install

Usage
-----
* A hello world example:

        >>> from akpytemp import Template
        >>> Template('Hello {# world #}, world='world')
        'Hello world'

* More complex usage

    <code>12daysofxmas.template</code>

        {#
            def ordinal(n):
                if 10 < n < 14: return u'%sth' % n
                if n % 10 == 1: return u'%sst' % n
                if n % 10 == 2: return u'%snd' % n
                if n % 10 == 3: return u'%srd' % n
                return u'%sth' % n                      #}
        {% for d in xrange(1, 13) %}
        On the {# ordinal(d) #} day of Christmas,
        my true love sent to me
        {% if d == 12 %}Twelve drummers drumming,
        {% end %}{% if d >= 11 %}Eleven pipers piping,
        {% end %}{% if d >= 10 %}Ten lords a-leaping,
        {% end %}{% if d >= 9  %}Nine ladies dancing,
        {% end %}{% if d >= 8  %}Eight maids a-milking,
        {% end %}{% if d >= 7  %}Seven swans a-swimming,
        {% end %}{% if d >= 6  %}Six geese a-laying,
        {% end %}{% if d >= 5  %}Five golden rings,
        {% end %}{% if d >= 4  %}Four calling birds,
        {% end %}{% if d >= 3  %}Three French hens,
        {% end %}{% if d >= 2  %}Two turtle doves,
        {% end %}{% if d == 1  %}A{% else %}And a{% end %} partridge in a pear tree.
        {% end %}    

Rendered result by running <code>python template.py test/12daysofxmas.template</code>

    On the 1st day of Christmas,
    my true love sent to me
    A partridge in a pear tree.

    On the 2nd day of Christmas,
    my true love sent to me
    Two turtle doves,
    And a partridge in a pear tree.

    On the 3rd day of Christmas,
    my true love sent to me
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 4th day of Christmas,
    my true love sent to me
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 5th day of Christmas,
    my true love sent to me
    Five golden rings,
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 6th day of Christmas,
    my true love sent to me
    Six geese a-laying,
    Five golden rings,
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 7th day of Christmas,
    my true love sent to me
    Seven swans a-swimming,
    Six geese a-laying,
    Five golden rings,
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 8th day of Christmas,
    my true love sent to me
    Eight maids a-milking,
    Seven swans a-swimming,
    Six geese a-laying,
    Five golden rings,
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 9th day of Christmas,
    my true love sent to me
    Nine ladies dancing,
    Eight maids a-milking,
    Seven swans a-swimming,
    Six geese a-laying,
    Five golden rings,
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 10th day of Christmas,
    my true love sent to me
    Ten lords a-leaping,
    Nine ladies dancing,
    Eight maids a-milking,
    Seven swans a-swimming,
    Six geese a-laying,
    Five golden rings,
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 11th day of Christmas,
    my true love sent to me
    Eleven pipers piping,
    Ten lords a-leaping,
    Nine ladies dancing,
    Eight maids a-milking,
    Seven swans a-swimming,
    Six geese a-laying,
    Five golden rings,
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

    On the 12th day of Christmas,
    my true love sent to me
    Twelve drummers drumming,
    Eleven pipers piping,
    Ten lords a-leaping,
    Nine ladies dancing,
    Eight maids a-milking,
    Seven swans a-swimming,
    Six geese a-laying,
    Five golden rings,
    Four calling birds,
    Three French hens,
    Two turtle doves,
    And a partridge in a pear tree.

* Built-in functions

    There are many built-in functions available to use in template rendering,
    simply call them like you would expect in Python, the methods in the
    template instance will be invoked. For example,

        {# name() #}

    will give the name of the template file being rendered.
    It is also possible to include template files within a template, this is
    done by simply using

        {# include('path/to/another_template_file') #}

    The namespaces of the included file will also become available in the
    parent file.
    To call built-in functions that belongs to the parent template, simply use

        {# parent.name() #}

    It is possible to extend build-in functions by subclassing Template, any
    member methods with a name that does not start with '_' will get included
    for the template.

* Error display

    *akpytemp* has a user friendly error display when an syntax error or an
    execution exception is caught. It gives a part of your source code
    highlighting the line that raised the exception with colour output.

        **  Error Occured in file "src/shifter.v":
        NameError: name 'accu_init_str' is not defined
        **  Source:
             64 | ...
             65 |     else
             66 |     begin
        -->  67 |         accu = {# accu_init_str #};
             68 |         accu_prev = {# accu_init_str #};
             69 |     end
             70 | ...

