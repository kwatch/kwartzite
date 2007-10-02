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
        self.stmt_list       = stmt_list
        self.elem_info_table = elem_info_table
        self.filename        = filename



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

