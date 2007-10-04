###
### $Rev$
### $Release$
### $Copyright$
###


import re
import kwartzite.config as config
from kwartzite.util import isword, OrderedDict, define_properties
from kwartzite.parser import Parser, ParseError, TemplateInfo



class TagInfo(object):


    def __init__(self, *args):
        self.string      = args[0]
        self.head_space  = args[1]
        self.is_etag     = args[2] # == '/' and '/' or ''
        self.name        = args[3]
        self.attr_str    = args[4]
        self.extra_space = args[5]
        self.is_empty    = args[6] # == '/' and '/' or ''
        self.tail_space  = args[7]
        self.linenum     = args[8]


    def set_name(self, tagname):
        self.name = tagname
        self.rebuild_string()


    def rebuild_string(self, attr=None):
        if attr:
            buf = []
            for space, name, value in attr:
                buf.extend((space, name, '="', value, '"', ))
            self.attr_str = ''.join(buf)
        t = (self.head_space or '', self.is_etag and '</' or '<',
             self.name, self.attr_str, self.extra_space,
             self.is_empty and '/>' or '>', self.tail_space or '')
        self.string = ''.join(t)


    def clear_as_dummy_tag(self):      # delete <span> tag
        self.name = None
        if self.head_space is not None and self.tail_space is not None:
            self.head_space = self.tail_space = None


    def _inspect(self):
        return repr([ self.head_space, self.is_etag, self.name, self.attr_str,
                      self.extra_space, self.is_empty, self.tail_space ])



class AttrInfo(object):


    _pattern = re.compile(r'(\s+)([-:_\w]+)="([^"]*?)"')


    def __init__(self, attr_str):
        self.names  = names  = []
        self.values = values = {}
        self.spaces = spaces = {}
        for m in AttrInfo._pattern.finditer(attr_str):
            space = m.group(1)
            name  = m.group(2)
            value = m.group(3)
            self.set(name, value, space)


    def has(self, name):
        return self.values.has_key(name)


    def __getitem__(self, name):
        return self.values[name]


    def __setitem__(self, name, value):
        self.set(name, value, ' ')


    def get(self, name, default=None):
        return self.values.get(name, default)


    def set(self, name, value, space=' '):
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
        self.stag    = stag      # TagInfo
        self.etag    = etag      # TagInfo
        self.cont   = cont_stmts     # list of Statement
        self.attr    = attr      # AttrInfo
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



class TextParser(Parser):
    """
    convert presentation data (html) into a list of Statement.
    notice that TextConverter class hanlde html file as text format, not html format.
    """


    _property_descriptions = (
        ('dattr'    , config.DATTR    , 'directive attribute name'),
        #('encoding' , config.ENCODING , 'encoding name'),
        ('delspan'  , config.DELSPAN  , 'delete dummy <span> tag or not'),
        ('idflag'   , config.IDFLAG   , 'marking detection policy (all/lower/upper/none)'),
    )
    define_properties(_property_descriptions)


    def __init__(self, dattr=None, encoding=None, idflag=None, delspan=None, escape=None, **properties):
        Parser.__init__(self, **properties)
        self.filename = None
        self.dattr    = dattr    is not None and dattr    or config.DATTR
        #self.encoding = encoding is not None and encoding or config.ENCODING
        self.idflag   = idflag   is not None and idflag   or config.IDFLAG
        if delspan is None: delspan = config.DELSPAN
        self.delspan  = delspan


    #FETCH_PATTERN = re.compile(r'(^[ \t]*)?<(/?)([-:_\w]+)((?:\s+[-:_\w]+="[^"]*?")*)(\s*)(/?)>([ \t]*\r?\n)?')
    FETCH_PATTERN = re.compile(r'([ \t]*)<(/?)([-:_\w]+)((?:\s+[-:_\w]+="[^"]*?")*)(\s*)(/?)>([ \t]*\r?\n)?')


    def _create_fetch_generator(self, input, pattern):
        pos = 0
        linenum = 1
        linenum_delta = 0
        prev_tagstr = ''
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
            tag = TagInfo(g(0), head_space, g(2), g(3), g(4), g(5), g(6), g(7), linenum)
            yield text, tag
        rest = pos == 0 and input or input[pos:]
        yield rest, None


    ## called from convert() and initialize converter object
    def _reset(self, input, filename):
        self.filename = filename
        self._elem_names = []
        self.elem_table = OrderedDict() # {}
        generator = self._create_fetch_generator(input, TextParser.FETCH_PATTERN)
        self._fetch = generator.next


    def parse(self, input, filename=''):
        self._reset(input, filename)
        stmt_list = []
        self._parse(stmt_list)
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
                    stmt_list.append(tag.string)
            ## empty tag
            elif tag.is_empty or self._skip_etag_p(tag.name):
                attr = AttrInfo(tag.attr_str)
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
                    stmt_list.append(tag.string)
            ## start tag
            else:
                attr = AttrInfo(tag.attr_str)
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
                    stmt_list.append(stag.string)
                    etag = self._parse(stmt_list, stag)  # recursive call
                    stmt_list.append(etag.string)
                else:
                    stmt_list.append(tag.string)
            ## continue while-loop
            text, tag = self._fetch()
        ## control flow reaches here only if _parse() is called by parse()
        if start_tag:
            msg = "'<%s>' is not closed." % start_tagname
            raise self._parse_error(msg, start_tag.linenum)
        if text:
            stmt_list.append(text)
        self.elem_table._keys = self._elem_names
        return None


    def _is_marking(self, directive_name):
        return directive_name in ('mark', 'text', 'node', 'attr', 'textattr', )


    def _parse_error(self, msg, linenum, column=None):
        return ParseError(msg, self.filename, linenum, column)


    def _create_elem(self, stag, etag, cont, attr):
        elem = ElementInfo(stag, etag, cont, attr)
        if self.delspan and elem.stag.name == 'span' and elem.attr.is_empty():
            elem.stag.clear_as_dummy_tag()
            if elem.etag:
                elem.etag.clear_as_dummy_tag()
        return elem


    _skip_etag_table = dict([ (tagname, True) for tagname in config.NO_ETAGS ])

    def _skip_etag_p(self, tagname):
        return TextParser._skip_etag_table.get(tagname) and True or False


    def _get_directive(self, attr, tag):
        if attr.has(self.dattr):        # kw:d="..."
            value = attr.get(value)
            if not value:
                attr.delete(self.dattr)
                tag.rebuild_string(attr)
                return None
            m = re.match(r'\w+:', value)
            if m:
                attr.delete(self.dattr)
                tag.rebuild_string(attr)
                directive_name = m.group(0)[0:-1]
                directive_arg  = value[len(directive_name)+1:]
                return Directive(directive_name, directive_arg, self.dattr, value)
            #else:
            #   return Directive('mark', value, self.dattr, value)
        elif attr.has('id'):            # id="..."
            value = attr.get('id')
            m = re.match(r'\w+:', value)
            if m:
                attr.delete('id')  # remove 'id' attribute
                tag.rebuild_string(attr)
                directive_name = m.group(0)[0:-1]
                directive_arg  = value[len(directive_name)+1:]
                return Directive(directive_name, directive_arg, 'id', value)
            elif isword(value):
                idflag = self.idflag
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
        stmt_list.append(elem.stag.string)
        self.__handle_directive_text(directive, elem, stmt_list)


    def __handle_directive_text(self, directive, elem, stmt_list):
        expr = Expression(None, name=directive.arg, kind='text')
        stmt_list.extend((expr, elem.etag.string, ))


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
        if not stag.is_empty:
            if elem.cont:
                stmt_list.extend(elem.cont)
            stmt_list.append(elem.etag.string)


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
        stmt_list.append(elem.stag.string)
        stmt_list.append(Expression(code))
        stmt_list.append(elem.etag.string)


    def _handle_directive_dummy(self, directive, elem, stmt_list):
        pass   # ignore element

