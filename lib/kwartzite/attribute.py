###
### $Rev$
### $Release$
### $Copyright$
###


from kwartzite.util import NULL



class Attribute(object):


    def __init__(self, arg=None):
        if isinstance(arg, dict):
            D = arg
            L = D.keys().sort()
        elif isinstance(arg, (tuple, list)):
            D = {}
            L = []
            for T in arg:
                name, value = T
                D[name] = value
                L.append(name)
                #if not D.has_key(name): L.append(name)
        else:
            D = {}
            L = []
        self._values = D
        self._names = L
        self._modified = False
        self.__getitem__ = D.__getitem__   # for performance


    def __setitem__(self, name, value):
        if not self._values.has_key(name):
            self._names.append(name)
        self._values[name] = value
        self._modified = True
        return value


    def __getitem__(self, name):
        return self._dict[name]


    def __delitem__(self, name):
        if self._values.has_key(name):
            del self._dict[name]
            self._names.remove(value)
            self._modified = true


    def append_to(self, buf, nullobj=None):
        _values = self._values
        for name in self._names:
            val = _values[name]
            if val is not nullobj:
                buf.extend((' ', name, '="', val, '"'))


    def to_string(self):
        buf = []
        self.append_to(buf)
        return ''.join(buf)


    def names(self):
        return self._names[:]


    def has_name(self, name):
        return self._values.has_key(name)


    def __iter__(self):
        _values = self._values
        return [ (name, _values[name]) for name in self._names ].__iter__()


    def __repr__(self):
        s = ''.join([ " %s=%s" % (name, repr(value)) for name, value in self ])
        return "<Attribute%s _modified=%s>" % (s, self._modified)


    ## dict compatible methods


    def get(self, name, default=None):
        return self._values.get(name, default)


    def keys(self):
        return self._names[:]


    def items(self):
        _values = self._values
        return [ (name, _values[name]) for name in self._names ]


    def iteritems(self):
        return self.items()


    has_key = has_name


    def clear(self):
        if len(self._names) != 0:
            self._values.clear()
            self._names.clear()
            self._modified = True


    def pop(self, key, default=NULL):
        if self._values.has_key(key):
            self._names.remove(key)
            self._modified = True
            return self._values.pop(key)
        elif default is NULL:
            return self._values.pop(key)
        else:
            return self._values.pop(key, default)


    def __contains__(self, key):
        return self._values.has_key(key)


    def __len__(self):
        return lef(self._names)


    def setdefault(key, default=None):
        if self._values.has_key(key):
            return self._values[key]
        else:
            self._values[key] = default
            self._modified = True
            return default


    def update(attr, **kwargs):
        for key, val in attr.iteritems():
            self[key] = val
        for key, val in kwargs.iteritems():
            self[key] = val


    def copy(self):
        attr = Attribute()
        attr._values = self._values.copy()
        attr._names = self._names[:]
        attr._modified = self._modified
        attr.__getitem__ = attr._values.__getitem__



if __name__ == '__main__':
    pass
    attr = Attribute([('class','section'), ('id','sec1')])
    print dir(attr)
    print repr(attr)
    attr['title'] = '..description..'
    attr['class'] = 'chapter'
    print repr(attr)
