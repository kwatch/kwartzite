# -*- coding: utf-8 -*-

import sys
python2 = sys.version_info[0] == 2
python3 = sys.version_info[0] == 3


class SafeStr(str):
    pass


class Template(object):

    encoding = 'utf-8'

    def __getitem__(self, key):
        return self.__dict__.get(key)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def populate(self, values):
        d = self.__dict__
        for k in kwargs:
            d[k] = kwargs[k]

    def render(self, **kwargs):
        if kwargs:
            self.populate(kwargs)
        self._buf = _buf = []
        self._append = _buf.append
        self._extend = _buf.extend
        self.elem_DOCUMENT()
        return ''.join(self._buf)

    def elem_DOCUMENT(self):
        pass

    def echo(self, value):
        self._buf.append(self.escape(self.to_str(value)))

    def escape(self, s):
        if isinstance(s, SafeStr):
            return s
        return SafeStr(s)

    def to_str(self, value):
        if isinstance(value, str):
            return value
        if value is None:
            return ''
        if isinstance(value, unicode):
            return value.decode(self.encoding)
        return str(value)


def escape_html(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')#.replace("'", '&039;')


class HtmlTemplate(Template):
    escape = staticmethod(escape_html)


def _dummy():

    def checked(value):
        return value and SafeStr('checked="checked"') or None

    def selected(value):
        return value and SafeStr('selected="selected"') or None

    def disabled(value):
        return value and SafeStr('disabled="disabled"') or None

    def new_cycle(*values):
        def gen():
            _values = [ escape_html(v) for v in values ]
            n = len(_values)
            i = 0
            while True:
                yield _values[i]
                i += 1
                if i == n:
                    i = 0
        if python2: return gen().next
        if python3: return gen().__next__

    return locals()


html = type(sys)('kwartizte.html')
sys.modules['kwartzite.html'] = html
html.__dict__.update(_dummy())
html.HtmlTemplate = HtmlTemplate
html.escape = escape_html
del _dummy, HtmlTemplate
