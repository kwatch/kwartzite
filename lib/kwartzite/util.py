###
### $Rev$
### $Release$
### $Copyright$
###


import re


def to_str(val):
    if val is None: return ''
    if isinstance(val, (str, unicode)): return val
    return str(val)


def generate_tostrfunc(encoding):
    def to_str(val):
        if val is None: return ''
        if isinstance(val, str): return val
        if isinstance(val, unicode): return val.encode(encoding)
        return str(val)
    return to_str



_escape_table = { '<':'&lt;', '>':'&gt;', '&':'&amp;', '"':'&quot;', "'":'&#039;'}
_escape_callable = lambda m: _escape_table[m.group(0)]
_escape_pattern = re.compile(r'[<>&"]')

def escape_xml(string):
    _escape_pattern.sub(_escape_callale, s)

h = escape_xml


def escape_xml2(string):
    return string.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;').replace('"', '&quot;')



_quote_table = { "'":"\\'", '"':'\\"', '\\':'\\\\' }
_quote_callable = lambda m: _quote_table[m.group(0)]
_quote_pattern = re.compile(r"['\\]")
_qquote_pattern = re.compile(r'["\\]')

def quote(string):
    return _quote_pattern.sub(_quote_callable, string)

def qquote(string):
    return _qquote_pattern.sub(_quote_callable, string)



_isword_pattern = re.compile('^\w+$')

def isword(s):
    return bool(_isword_pattern.match(s))



class OrderedDict(dict):


    def __init__(self, *args):
        dict.__init__(self, *args)
        self._keys = []


    def __setitem__(self, key, value):
        if self.has_key(key):
            self._keys.remove(key)
        self._keys.append(key)
        return dict.__setitem__(self, key, value)


    def keys(self):
        return self._keys[:]


    def __iter__(self):
        return self._keys.__iter__()


    def iteritems(self):
        return [ (k, self[k]) for k in self._keys ].__iter__()


    def __delitem__(self, key):
        if self.has_key(key):
            self._keys.remove(key)
        return dict.__delitem__(self, key)


    def clear(self):
        self._keys = []
        dict.clear(self)


    def copy(self):
        new = dict.copy(self)
        new._keys = self._keys[:]
        return new


    def pop(self, key):
        if self.has_key(key):
            self._keys.remove(key)
        return dict.pop(self, key)


    def popitem(self, key):
        if self.has_key(key):
            self._keys.remove(key)
        return dict.pop(self, key)


    def update(self, other):
        if other:
            for key, val in other.iteritems():
                self[key] = value
