###
### $Rev$
### $Release$
### $Copyright$
###


from kwartzite import BaseError



class ParseError(BaseError):


    def __init__(self, message, filename=None, linenum=None, column=None):
        BaseError.__init__(self, message)
        self.filename = filename
        self.linenum = linenum
        self.column = column


    def to_string(self):
        "%s:%s:%s: %s: %s" % (self.filename, self.linenum, self.column,
                              self.__class__.__name__, self.message)



class TemplateInfo(object):


    def __init__(self, stmt_list, elem_info_table, filename=None):
        self.stmt_list       = self.pack(stmt_list)
        self.elem_info_table = elem_info_table
        self.filename        = filename
        for name, elem_info in self.elem_info_table.iteritems():
            if elem_info.cont_stmts:
                elem_info.cont_stmts = self.pack(elem_info.cont_stmts)


    def pack(self, stmt_list):
        if not stmt_list or len(stmt_list) == 1:
            return stmt_list
        pos = 0
        i = -1
        L = []
        for item in stmt_list:
            i += 1
            if isinstance(item, (str, unicode)):
                pass
            else:
                if pos < i:
                    L.append(''.join(stmt_list[pos:i]))
                pos = i + 1
                L.append(item)
        if pos <= i:
            L.append(''.join(stmt_list[pos:]))
        new_stmt_list = L
        return new_stmt_list



class Parser(object):


    def __init__(self, **properties):
        self.properties = properties


    def parse(self, input, filename=None, **kwargs):
        """parse input string and return TemplateInfo object."""
        raise NotImplementedError("%s#parser() is not implemented." % self.__class__.__name__)


    def parse_file(self, filename, **kwargs):
        """parse template file and return TemplateInfo object."""
        input = open(filename).read()
        return self.parse(input, filename, **kwargs)
