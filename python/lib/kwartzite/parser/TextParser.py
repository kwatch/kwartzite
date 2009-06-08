###
### $Rev$
### $Release$
### $Copyright$
###


import re
from kwartzite.config import ParserConfig, TextParserConfig
from kwartzite.util import escape_xml, h, isword, OrderedDict, define_properties
from kwartzite.parser import Parser, ParseError, TemplateInfo



class TagInfo(object):


    def __init__(self, tagname, attr, is_etag=None, is_empty=None, linenum=None,
                 string=None, head_space=None, tail_space=None, extra_space=None):
        self.name        = tagname
        self.attr        = AttrInfo(attr)
        self.is_etag     = is_etag and '/' or ''
        self.is_empty    = is_empty and '/' or ''
        self.linenum     = linenum
        self.string      = string
        self.head_space  = head_space
        self.tail_space  = tail_space
        self.extra_space = extra_space
        #if isinstance(attr, (str, unicode)):
        #    self.attr_str = attr
        #elif isinstance(attr, (tuple, list)):
        #    self.attr_str = ''.join([ ' %s="%s"' % (t[0], t[1]) for t in attr ])
        #elif isinstance(attr, dict):
        #    self.attr_str = ''.join([ ' %s="%s"' % (k, v) for k, v in attr.iteritems() ])
        #else:
        #    self.attr_str = attr


    def set_attr(self, attr):
        self.attr = attr
        self.rebuild_string(attr)


#    def rebuild_string(self, attr=None):
#        if attr:
#            buf = []
#            for space, name, value in attr:
#                buf.extend((space, name, '="', value, '"', ))
#            self.attr_str = ''.join(buf)
#        t = (self.head_space or '', self.is_etag and '</' or '<',
#             self.name, self.attr_str or '', self.extra_space or '',
#             self.is_empty and '/>' or '>', self.tail_space or '')
#        self.string = ''.join(t)
#        return self.string


    def clear_as_dummy_tag(self):      # delete <span> tag
        self.name = None
        if self.head_space is not None and self.tail_space is not None:
            self.head_space = self.tail_space = None


#    def _inspect(self):
#        return repr([ self.head_space, self.is_etag, self.name, self.attr_str,
#                      self.extra_space, self.is_empty, self.tail_space ])


    def _to_string(self):
        buf = [self.head_space or '', self.is_etag and '</' or '<', self.name]
        for space, name, value in self.attr:
            buf.extend((space, name, '="', value, '"', ))
        buf.extend((self.extra_space or '', self.is_empty and '/>' or '>', self.tail_space or ''))
        return ''.join(buf)


    def to_string(self):
        if not self.string:
            self.string = self._to_string()
        return self.string


    #__repr__ = to_string
    def __repr__(self):
        buf = [self.head_space or '', self.is_etag and '</' or '<', self.name]
        for space, name, value in self.attr:
            buf.extend((space, name, '="', value, '"', ))
        if self.linenum is not None: buf.extend((' linenum="', str(self.linenum), '"'))
        buf.extend((self.extra_space or '', self.is_empty and '/>' or '>', self.tail_space or ''))
        return ''.join(buf)



class AttrInfo(object):


    def __init__(self, arg=None, escape=False):
        self.names  = names  = []
        self.values = values = {}
        self.spaces = spaces = {}
        if arg is not None:
            if isinstance(arg, (str, unicode)):
                self.parse_str(arg)
            elif isinstance(arg, (tuple, list)):
                self.parse_tuples(arg)
            elif isinstance(arg, dict):
                self.parse_dict(arg)


    _pattern = re.compile(r'(\s+)([-:_\w]+)="([^"]*?)"')


    def parse_str(self, attr_str, escape=False):
        for m in AttrInfo._pattern.finditer(attr_str):
            space = m.group(1)
            name  = m.group(2)
            value = m.group(3)
            self.set(name, value, space, escape)


    def parse_tuples(self, tuples, escape=False):
        for t in tuples:
            n = len(t)
            if n == 2:
                name, value = t
                space = ' '
            elif n == 3:
                space, name, value = t
            else:
                assert False, "** t=%s" % repr(t)
            self.set(name, value, space, escape)


    def parse_dict(self, dictionary, escape=False):
        for name, value in dictionary.iteritems():
            self.set(name, value, ' ', escape)


    def has(self, name):
        return self.values.has_key(name)


    def __getitem__(self, name):
        return self.values[name]


    def __setitem__(self, name, value):
        self.set(name, value, ' ')


    def get(self, name, default=None):
        return self.values.get(name, default)


    def set(self, name, value, space=' ', escape=False):
        if escape:
            name  = escape_xml(name)
            value = escape_xml(value)
        if not self.values.has_key(name):
            self.names.append(name)
            self.spaces[name] = space
        self.values[name] = value


    def __iter__(self):
        return [ (self.spaces[k], k, self.values[k]) for k in self.names ].__iter__()


    def delete(self, name):
        if self.has(name):
            self.names.remove(name)
            self.spaces.pop(name)
            return self.values.pop(name)
        return None


    def is_empty(self):
        return len(self.names) == 0



class ElementInfo(object):


    def __init__(self, stag, etag, cont_stmts, attr):
        self.stag = stag      # TagInfo
        self.etag = etag      # TagInfo
        self.cont = cont_stmts     # list of Statement
        self.attr = attr      # AttrInfo
        self.name = None
        self.directive = None


    def cont_text_p(self):
        L = self.cont
        return L and len(L) == 1 and isinstance(L[0], (str, unicode))
        #if not self.cont:
        #    return False
        #for item in self.cont:
        #    if not isinstance(item, (str, unicode)):
        #        return False
        #return True



class Expression(object):


    def __init__(self, code_str, name=None, kind='native'):
        self.code = code_str
        self.name = name
        self.kind = kind



class Directive(object):


    def __init__(self, directive_name, directive_arg, attr_name, attr_value, linenum=None):
        self.name       = directive_name
        self.arg        = directive_arg
        self.attr_name  = attr_name
        self.attr_value = attr_value
        self.linenum    = linenum


    def attr_string(self):
        return '%s="%s"' % (self.attr_name, self.attr_value)



class BaseParser(Parser, ParserConfig):


    _property_descriptions = (
        ('dattr'    , 'str'  , 'directive attribute name'),
        ('encoding' , 'str'  ,  'encoding name'),
        ('delspan'  , 'bool' , 'delete dummy <span> tag or not'),
        #('idflag'   , 'str'  , 'marking detection policy (all/lower/upper/none)'),
        ('idflag'   , '{all|upper|lower|none}'  , 'marking detection policy'),
        #('idflag'   , 'all/lower/upper/none'  , 'marking detection policy'),
    )
    define_properties(_property_descriptions)


    def __init__(self, dattr=None, encoding=None, idflag=None, delspan=None, escape=None, **properties):
        Parser.__init__(self, **properties)
        self.filename = None
        if dattr    is not None:  self.DATTR    = dattr
        if encoding is not None:  self.ENCODING = encoding
        if idflag   is not None:  self.IDFLAG   = idflag
        if delspan  is not None:  self.DELSPAN  = delspan


    def _setup(self, input, filename):
        self.filename = filename
        self._elem_names = []
        self.elem_table = OrderedDict() # {}


    def _teardown(self):
        self.elem_table._keys = self._elem_names


    def parse(self, input, filename=''):
        self._setup(input, filename)
        stmt_list = []
        self._parse(stmt_list)
        self._teardown()
        return TemplateInfo(stmt_list, self.elem_table, filename)


    def _parse(self, stmt_list, start_tag=None):
        if start_tag:
            start_tagname = start_tag.name
            start_linenum = start_tag.linenum
        else:
            start_tagname = ""
            start_linenum = 1
        ##
        text, tag = self._fetch()
        while tag:
            ## prev text
            if text:
                stmt_list.append(text)
            ## end tag
            if tag.is_etag:
                if tag.name == start_tagname:
                    return tag
                else:
                    stmt_list.append(tag.to_string())
            ## empty tag
            elif tag.is_empty or self._skip_etag_p(tag.name):
                attr = tag.attr
                directive = self._get_directive(attr, tag)
                if directive:
                    directive.linenum = tag.linenum
                    if self._is_marking(directive.name):
                        elem_name = directive.arg
                        self._elem_names.append(elem_name)
                    stag = tag
                    etag = None
                    cont = []
                    elem = self._create_elem(stag, etag, cont, attr)
                    self._handle_directive(directive, elem, stmt_list)
                else:
                    stmt_list.append(tag.to_string())
            ## start tag
            else:
                attr = tag.attr
                directive = self._get_directive(attr, tag)
                if directive:
                    directive.linenum = tag.linenum
                    if self._is_marking(directive.name):
                        elem_name = directive.arg
                        self._elem_names.append(elem_name)
                    stag = tag
                    cont = []
                    etag = self._parse(cont, stag)
                    elem = self._create_elem(stag, etag, cont, attr)
                    self._handle_directive(directive, elem, stmt_list)
                elif tag.name == start_tagname:
                    stag = tag
                    stmt_list.append(stag.to_string())
                    etag = self._parse(stmt_list, stag)  # recursive call
                    stmt_list.append(etag.to_string())
                else:
                    stmt_list.append(tag.to_string())
            ## continue while-loop
            text, tag = self._fetch()
        ## control flow reaches here only if _parse() is called by parse()
        if start_tag:
            msg = "'<%s>' is not closed." % start_tagname
            raise self._parse_error(msg, start_tag.linenum)
        if text:
            stmt_list.append(text)
        return None


    def _is_marking(self, directive_name):
        return directive_name in ('mark', 'text', 'node', 'attr', 'textattr', )


    def _parse_error(self, msg, linenum, column=None):
        return ParseError(msg, self.filename, linenum, column)


    def _create_elem(self, stag, etag, cont, attr):
        elem = ElementInfo(stag, etag, cont, attr)
        if self.DELSPAN and elem.stag.name == 'span' and elem.attr.is_empty():
            elem.stag.clear_as_dummy_tag()
            if elem.etag:
                elem.etag.clear_as_dummy_tag()
        return elem


    _skip_etag_table = dict([ (tagname, True) for tagname in ParserConfig.NO_ETAGS ])


    def _skip_etag_p(self, tagname):
        return TextParser._skip_etag_table.get(tagname) and True or False


    def _get_directive(self, attr, tag):
        if attr.has(self.DATTR):        # kw:d="..."
            value = attr.get(value)
            if not value:
                attr.delete(self.DATTR)
                tag.string = None #tag.rebuild_string(attr)
                return None
            m = re.match(r'\w+:', value)
            if m:
                attr.delete(self.DATTR)
                tag.string = None #tag.rebuild_string(attr)
                directive_name = m.group(0)[0:-1]
                directive_arg  = value[len(directive_name)+1:]
                return Directive(directive_name, directive_arg, self.DATTR, value)
            #else:
            #   return Directive('mark', value, self.dattr, value)
        elif attr.has('id'):            # id="..."
            value = attr.get('id')
            m = re.match(r'\w+:', value)
            if m:
                attr.delete('id')  # remove 'id' attribute
                tag.string = None #tag.rebuild_string(attr)
                directive_name = m.group(0)[0:-1]
                directive_arg  = value[len(directive_name)+1:]
                return Directive(directive_name, directive_arg, 'id', value)
            elif isword(value):
                idflag = self.IDFLAG
                if idflag == 'all' or \
                   idflag == 'upper' and value[0].isupper() or \
                   idflag == 'lower' and value[0].islower():
                    return Directive('mark', value, 'id', value)
        return None


    def _handle_directive(self, directive, elem, stmt_list):
        func = getattr(self, '_handle_directive_%s' % directive.name, None)
        if not func:
            d = directive
            msg = '%s="%s": unknown directive.' % (d.attr_name, d.attr_value)
            raise self._parse_error(msg, d.linenum)
        is_empty_tag = elem.stag.is_empty
        if is_empty_tag and directive.name in ('text', 'textattr', 'value'):
            d = directive
            msg = '%s="%s": not available with empty tag.' % (d.attr_name, d.attr_value)
            raise self._parse_error(msg, d.linenum)
        elem.directive = directive
        func(directive, elem, stmt_list)


    def _check_mark_directive(self, directive, elem, stmt_list):
        name = directive.arg
        if not isword(name):
            d = directive
            msg = '%s="%s": invalid marking name.' % (d.attr_name, d.attr_value)
            raise self._parse_error(msg, d.linenum)
        e = self.elem_table.get(name)
        if e:
            d = directive
            msg = '%s="%s": marking name duplicated (found at line %s).' % \
                  (d.attr_name, d.attr_value, d.linenum)
            raise self._parse_error(msg, d.linenum)
        ## common operation
        name = directive.arg
        elem.name = name
        self.elem_table[name] = elem


    def _handle_directive_mark(self, directive, elem, stmt_list):
        self._check_mark_directive(directive, elem, stmt_list)
        stmt_list.append(elem)


    def _handle_directive_text(self, directive, elem, stmt_list):
        self._check_mark_directive(directive, elem, stmt_list)
        stmt_list.append(elem.stag.to_string())
        self.__handle_directive_text(directive, elem, stmt_list)


    def __handle_directive_text(self, directive, elem, stmt_list):
        expr = Expression(None, name=directive.arg, kind='text')
        stmt_list.extend((expr, elem.etag.to_string(), ))


    def __handle_directive_attr(self, directive, elem, stmt_list):
        expr = Expression(None, name=directive.arg, kind='attr')
        stag = elem.stag
        stmt_list.extend((
            stag.head_space or '', '<', stag.name, expr,
            stag.extra_space or '', stag.is_empty and '/>' or '>',
            stag.tail_space or '',
            ))


    def _handle_directive_attr(self, directive, elem, stmt_list):
        self._check_mark_directive(directive, elem, stmt_list)
        self.__handle_directive_attr(directive, elem, stmt_list)
        if not elem.stag.is_empty:
            if elem.cont:
                stmt_list.extend(elem.cont)
            stmt_list.append(elem.etag.to_string())


    def _handle_directive_textattr(self, directive, elem, stmt_list):
        self._check_mark_directive(directive, elem, stmt_list)
        self.__handle_directive_attr(directive, elem, stmt_list)
        self.__handle_directive_text(directive, elem, stmt_list)


    def _handle_directive_node(self, directive, elem, stmt_list):
        self._check_mark_directive(directive, elem, stmt_list)
        expr = Expression(None, name=directive.arg, kind='node')
        stmt_list.append(expr)


    def _handle_directive_value(self, directive, elem, stmt_list):
        code = directive.arg
        stmt_list.append(elem.stag.to_string())
        stmt_list.append(Expression(code))
        stmt_list.append(elem.etag.to_string())


    def _handle_directive_dummy(self, directive, elem, stmt_list):
        pass   # ignore element



class TextParser(BaseParser, TextParserConfig):
    """
    convert presentation data (html) into a list of Statement.
    notice that TextConverter class hanlde html file as text format, not html format.
    """

    #FETCH_PATTERN = re.compile(r'(^[ \t]*)?<(/?)([-:_\w]+)((?:\s+[-:_\w]+="[^"]*?")*)(\s*)(/?)>([ \t]*\r?\n)?')
    FETCH_PATTERN = re.compile(r'([ \t]*)<(/?)([-:_\w]+)((?:\s+[-:_\w]+="[^"]*?")*)(\s*)(/?)>([ \t]*\r?\n)?')


    def _create_fetch_generator(self, input, pattern):
        pos = 0
        linenum = 1
        linenum_delta = 0
        prev_tagstr = ''
        column = None
        for m in pattern.finditer(input):
            start = m.start()
            if start == 0 or input[start-1] == "\n":  # beginning of line
                head_space = m.group(1)
            else:
                head_space = None
                start += len(m.group(1))
            text = input[pos:start]
            pos = m.end()
            linenum += text.count("\n") + prev_tagstr.count("\n")
            prev_tagstr = m.group(0)
            g = m.group
            string, is_etag, tagname, attr_str, extra_space, is_empty, tail_space = \
                g(0), g(2), g(3), g(4), g(5), g(6), g(7)
            tag = TagInfo(tagname, attr_str, is_etag, is_empty, linenum,
                          string, head_space, tail_space, extra_space)
            yield text, tag
        rest = pos == 0 and input or input[pos:]
        yield rest, None


    ##
    def _setup(self, input, filename):
        BaseParser._setup(self, input, filename)
        generator = self._create_fetch_generator(input, TextParser.FETCH_PATTERN)
        self._fetch = generator.next
