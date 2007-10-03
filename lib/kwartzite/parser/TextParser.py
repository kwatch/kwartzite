###
### $Rev$
### $Release$
### $Copyright$
###


import re
import kwartzite.config as config
from kwartzite.util import isword, OrderedDict
from kwartzite.parser import Parser, ParseError, TemplateInfo



class TagInfo(object):


    def __init__(self, *args):
        self.prev_text   = args[0]
        self.tag_text    = args[1]
        self.head_space  = args[2]
        self.is_etag     = args[3] # == '/' and '/' or ''
        self.tagname     = args[4]
        self.attr_str    = args[5]
        self.extra_space = args[6]
        self.is_empty    = args[7] # == '/' and '/' or ''
        self.tail_space  = args[8]
        self.linenum     = args[9]


    def set_tagname(self, tagname):
        self.tagname = tagname
        self.rebuild_tag_text()


    def rebuild_tag_text(self, attr_info=None):
        if attr_info:
            buf = []
            for space, name, value in attr_info:
                buf.extend((space, name, '="', value, '"', ))
            self.attr_str = ''.join(buf)
        t = (self.head_space or '', '<', self.is_etag and '/' or '',
             self.tagname, self.attr_str, self.extra_space,
             self.is_empty and '/' or '', '>', self.tail_space or '')
        self.tag_text = ''.join(t)


    def clear_as_dummy_tag(self):      # delete <span> tag
        self.tagname = None
        if self.head_space is not None and self.tail_space is not None:
            self.head_space = self.tail_space = None


    def _inspect(self):
        return [ self.prev_text, self.head_space, self.is_etag, self.tagname,
                 self.attr_str, self.extra_space, self.is_empty, self.tail_space ]



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


    def __init__(self, stag_info, etag_info, cont_stmts, attr_info):
        self.stag_info    = stag_info      # TagInfo
        self.etag_info    = etag_info      # TagInfo
        self.cont_stmts   = cont_stmts     # list of Statement
        self.attr_info    = attr_info      # AttrInfo
        self.name = None
        self.directive = None


    def cont_text_p(self):
        L = self.cont_stmts
        return L and len(L) == 1 and isinstance(L[0], (str, unicode))
        #if not self.cont_stmts:
        #    return False
        #for item in self.cont_stmts:
        #    if not isinstance(item, (str, unicode)):
        #        return False
        #return True



class Expression(object):


    def __init__(self, code_str):
        self.code = code_str



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


    def __init__(self, dattr=None, encoding=None, idflag=None, delspan=None, escape=None, **properties):
        Parser.__init__(self, **properties)
        self.filename = None
        self.dattr    = dattr    is not None and dattr    or config.DATTR
        self.encoding = encoding is not None and encoding or config.ENCODING
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
            taginfo = TagInfo(text, g(0), head_space, g(2), g(3), g(4), g(5), g(6), g(7), linenum)
            yield taginfo
        self._rest = pos == 0 and input or input[pos:]
        yield None


    ## called from convert() and initialize converter object
    def _reset(self, input, filename):
        self.filename = filename
        self._rest = None
        self._elem_names = []
        self.elem_info_table = OrderedDict() # {}
        generator = self._create_fetch_generator(input, TextParser.FETCH_PATTERN)
        self._fetch = generator.next


    def parse(self, input, filename=''):
        self._reset(input, filename)
        stmt_list = []
        self._parse(stmt_list)
        return TemplateInfo(stmt_list, self.elem_info_table, filename)


    def _parse(self, stmt_list, start_tag_info=None):
        if start_tag_info:
            start_tagname = start_tag_info.tagname
            start_linenum = start_tag_info.linenum
        else:
            start_tagname = ""
            start_linenum = 1
        ##
        taginfo = self._fetch()
        while taginfo:
            ## prev text
            prev_text = taginfo.prev_text
            if prev_text:
                stmt_list.append(prev_text)
            ## end tag
            if taginfo.is_etag:
                if taginfo.tagname == start_tagname:
                    return taginfo
                else:
                    stmt_list.append(taginfo.tag_text)
            ## empty tag
            elif taginfo.is_empty or self._skip_etag_p(taginfo.tagname):
                attr_info = AttrInfo(taginfo.attr_str)
                directive = self._get_directive(attr_info, taginfo)
                if directive:
                    directive.linenum = taginfo.linenum
                    if self._is_marking(directive.name):
                        elem_name = directive.arg
                        self._elem_names.append(elem_name)
                    stag_info = taginfo
                    etag_info = None
                    cont_stmts = []
                    elem_info = self._create_elem_info(stag_info, etag_info, cont_stmts, attr_info)
                    self._handle_directive(directive, elem_info, stmt_list)
                else:
                    stmt_list.append(taginfo.tag_text)
            ## start tag
            else:
                attr_info = AttrInfo(taginfo.attr_str)
                directive = self._get_directive(attr_info, taginfo)
                if directive:
                    directive.linenum = taginfo.linenum
                    if self._is_marking(directive.name):
                        elem_name = directive.arg
                        self._elem_names.append(elem_name)
                    stag_info = taginfo
                    cont_stmts = []
                    etag_info = self._parse(cont_stmts, stag_info)
                    elem_info = self._create_elem_info(stag_info, etag_info, cont_stmts, attr_info)
                    self._handle_directive(directive, elem_info, stmt_list)
                elif taginfo.tagname == start_tagname:
                    stag_info = taginfo
                    stmt_list.append(stag_info.tag_text)
                    etag_info = self._parse(stmt_list, stag_info)  # recursive call
                    stmt_list.append(etag_info.tag_text)
                else:
                    stmt_list.append(taginfo.tag_text)
            ## continue while-loop
            taginfo = self._fetch()
        ## control flow reaches here only if _parse() is called by parse()
        if start_tag_info:
            msg = "'<%s>' is not closed." % start_tagname
            raise self._parse_error(msg, start_tag_info.linenum)
        if self._rest:
            stmt_list.append(self._rest)
        self.elem_info_table._keys = self._elem_names
        return None


    def _is_marking(self, directive_name):
        return directive_name in ('mark', 'text', 'node', 'attr', 'textattr', )


    def _parse_error(self, msg, linenum, column=None):
        return ParseError(msg, self.filename, linenum, column)


    def _create_elem_info(self, stag_info, etag_info, cont_stmts, attr_info):
        elem_info = ElementInfo(stag_info, etag_info, cont_stmts, attr_info)
        if self.delspan and elem_info.stag_info.tagname == 'span' and elem_info.attr_info.is_empty():
            elem_info.stag_info.clear_as_dummy_tag()
            if elem_info.etag_info:
                elem_info.etag_info.clear_as_dummy_tag()
        return elem_info


    _skip_etag_table = dict([ (tagname, True) for tagname in config.NO_ETAGS ])

    def _skip_etag_p(self, tagname):
        return TextParser._skip_etag_table.get(tagname) and True or False


    def _get_directive(self, attr_info, taginfo):
        if attr_info.has(self.dattr):        # kw:d="..."
            value = attr_info.get(value)
            if not value:
                attr_info.delete(self.dattr)
                taginfo.rebuild_tag_text(attr_info)
                return None
            m = re.match(r'\w+:', value)
            if m:
                attr_info.delete(self.dattr)
                taginfo.rebuild_tag_text(attr_info)
                directive_name = m.group(0)[0:-1]
                directive_arg  = value[len(directive_name)+1:]
                return Directive(directive_name, directive_arg, self.dattr, value)
            #else:
            #   return Directive('mark', value, self.dattr, value)
        elif attr_info.has('id'):            # id="..."
            value = attr_info.get('id')
            m = re.match(r'\w+:', value)
            if m:
                attr_info.delete('id')  # remove 'id' attribute
                taginfo.rebuild_tag_text(attr_info)
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


    def _handle_directive(self, directive, elem_info, stmt_list):
        func = getattr(self, '_handle_directive_%s' % directive.name, None)
        if not func:
            d = directive
            msg = '%s="%s": unknown directive.' % (d.attr_name, d.attr_value)
            raise self._parse_error(msg, d.linenum)
        is_empty_tag = elem_info.stag_info.is_empty
        if is_empty_tag and directive.name in ('text', 'textattr', 'value'):
            d = directive
            msg = '%s="%s": not available with empty tag.' % (d.attr_name, d.attr_value)
            raise self._parse_error(msg, d.linenum)
        elem_info.directive = directive
        func(directive, elem_info, stmt_list)


    def _handle_directive_mark(self, directive, elem_info, stmt_list):
        name = directive.arg
        elem_info.name = name
        if not isword(name):
            d = directive
            msg = '%s="%s": invalid marking name.' % (d.attr_name, d.attr_value)
            raise self._parse_error(msg, d.linenum)
        e = self.elem_info_table.get(name)
        if e:
            d = directive
            msg = '%s="%s": marking name duplicated (found at line %s).' % \
                  (d.attr_name, d.attr_value, e.tag_info.linenum)
            raise self._parse_error(msg, d.linenum)
        self.elem_info_table[name] = elem_info
        stmt_list.append(elem_info)


    _handle_directive_text     = _handle_directive_mark
    _handle_directive_node     = _handle_directive_mark
    _handle_directive_attr     = _handle_directive_mark
    _handle_directive_textattr = _handle_directive_mark


    def _handle_directive_value(self, directive, elem_info, stmt_list):
        code = directive.arg
        stmt_list.append(elem_info.stag_info.tag_text)
        stmt_list.append(Expression(code))
        stmt_list.append(elem_info.etag_info.tag_text)


    def _handle_directive_dummy(self, directive, elem_info, stmt_list):
        pass   # ignore element

