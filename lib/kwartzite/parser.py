###
### $Rev$
### $Release$
### $Copyright$
###

import re
import config
from util import isword, quote



class Parser(object):


    def parse(self, input, filename=None):
        raise NotImplementedError("%s#parser() is not implemented." % self.__class__.__name__)


    def parse_file(self, filename):
        input = open(filename).read()
        return self.parse(input, filename)



class ParsedData(object):


    def __init__(self, stmt_list, elem_info_table, filename=None):
        self.stmt_list       = stmt_list
        self.elem_info_table = elem_info_table
        self.filename        = filename



class ParseError(StandardError):


    def __init__(self, message, filename=None, linenum=None, column=None):
        StandardError.__init__(self, message)
        self.filename = filename
        self.linenum = linenum
        self.column = column


    def to_string(self):
        "%s:%s:%s: %s: %s" % (self.filename, self.linenum, self.column,
                              self.__class__.__name__, self.message)



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

    def cont_text_p(self):
        L = self.cont_stmts
        return L and len(L) == 1 and isinstance(L[0], (str, unicode))



class NativeExpression(object):


    def __init__(self, code_str):
        self.code = code_str



class Directive(object):


    def __init__(self, directive_name, directive_arg, attr_name, attr_value, linenum=None):
        self.name       = directive_name
        self.arg        = directive_arg
        self.attr_name  = attr_name
        self.attr_value = attr_value
        self.linenum    = linenum



##
## convert presentation data (html) into a list of Statement.
## notice that TextConverter class hanlde html file as text format, not html format.
##
class TextParser(Parser):


    def __init__(self, dattr=None, encoding=None, idflag=None, delspan=None, escape=None, **kwargs):
        Parser.__init__(self)
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
        return ParsedData(stmt_list, self.elem_info_table, filename)


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
                    if directive.name == 'mark':
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
                    if directive.name == 'mark':
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


    def _handle_directive_value(self, directive, elem_info, stmt_list):
        code = directive.arg
        stmt_list.append(elem_info.stag_info.tag_text)
        stmt_list.append(NativeExpression(code))
        stmt_list.append(elem_info.etag_info.tag_text)


    def _handle_directive_dummy(self, directive, elem_info, stmt_list):
        pass   # ignore element



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



import os

def q(string):
    s = quote(string)
    if s.endswith("\r\n"):
        return s[0:-2] + "\\r\\n"
    if s.endswith("\n"):
        return s[0:-1] + "\\n"
    return s



class Translator(object):


    def __init__(self, encoding=None, **properties):
        self.encoding = encoding
        self.properties = properties


    def translate(self, parsed_data, **kwargs):
        raise NotImplementedError("%s#translate() is not implemented." % self.__class__.__name__)



class PythonTranslator(Translator):


    def translate(self, parsed_data, filename=None, classname=None, parent=None, encoding=None, **kwargs):
        if filename is None:
            filename = parsed_data.filename
        if classname is None:
            classname = self.build_classname(filename, **kwargs)
        if parent is None:
            parent = self.properties.get('parent', 'object')
        if encoding is None:
            encoding = self.encoding
        return self.generate_code(parsed_data, filename=filename, classname=classname, parent=parent, encoding=encoding, **kwargs)


    def build_classname(self, filename, prefix=None, postfix=None, **kwargs):
        s = os.path.basename(filename)
        #pos = s.rindex('.')
        #if pos > 0: s = s[0:pos]
        s = re.sub(r'[^\w]', '_', s)
        if not prefix:  prefix  = self.properties.get('prefix')
        if not postfix: postfix = self.properties.get('postfix')
        if prefix:  s = prefix + s
        if postfix: s = s + postfix
        classname = s
        return classname


    def generate_code(self, parsed_data, filename=None, classname=None, parent=None, encoding=None, **properties):
        stmt_list       = parsed_data.stmt_list
        elem_info_table = parsed_data.elem_info_table
        buf = []
        if encoding:
            buf.extend(('# -*- coding: ', encoding, " -*-\n", ))
        if filename:
            buf.extend(('## generated from ', filename, '\n', ))
        buf.extend((
            '\n'
            'from kwartzite.attribute import Attribute\n',
            ))
        if encoding:
            buf.extend((
            'from kwartzite.util import escape_xml, generate_tostrfunc\n'
            'to_str = generate_tostrfunc(', repr(encoding), ')\n'
            ))
        else:
            buf.extend((
            'from kwartzite.util import escape_xml, to_str\n'
            ))
        buf.extend((
            'h = escape_xml\n'
            "__all__ = ['", classname, "', 'escape_xml', 'to_str', 'h', ]\n"
            '\n'
            'class ', classname, '(', parent, '):\n'
            '\n'
            '    def __init__(self, **_context):\n'
            '        for k, v in _context.iteritems():\n'
            '            setattr(self, k, v)\n'
            '        self._context = _context\n'
            '        self._buf = []\n'
            ))
        for name, elem_info in elem_info_table.iteritems():
            buf.extend(('        self.init_', name, '()\n', ))
        buf.extend((
            '\n'
            '    def create_document(self):\n'
            '        _buf = self._buf\n'
            ))
        self.expand_items(buf, stmt_list)
        buf.extend((
            "        return ''.join(_buf)\n"
            "\n",
            ))
        for name, elem_info in elem_info_table.iteritems():
            buf.extend(("    ## element '", name, "'\n\n", ))
            self.expand_init(buf, elem_info); buf.append("\n")
            self.expand_elem(buf, elem_info); buf.append("\n")
            self.expand_stag(buf, elem_info); buf.append("\n")
            self.expand_cont(buf, elem_info); buf.append("\n")
            self.expand_etag(buf, elem_info); buf.append("\n")
            buf.extend((
            "    _init_", name, " = init_", name, "\n"
            "    _elem_", name, " = elem_", name, "\n"
            "    _stag_", name, " = stag_", name, "\n"
            "    _cont_", name, " = cont_", name, "\n"
            "    _etag_", name, " = etag_", name, "\n"
            "\n",
            ))
        #buf.extend((
        #    "\n"
        #    "class ", classname, "(", classname, "_):\n"
        #    "    pass\n"
        #    "\n",
        #    ))
        return ''.join(buf)


    def expand_items(self, buf, stmt_list):
        pos = 0
        i = -1
        for item in stmt_list:
            i += 1
            if isinstance(item, (str, unicode)):
                pass
            else:
                if pos < i:
                    buf.extend(("        _buf.append('''",
                                q(''.join(stmt_list[pos:i])),
                                "''')\n", ))
                pos = i + 1
                if isinstance(item, ElementInfo):
                    elem_info = item
                    buf.extend(("        self.elem_", elem_info.name, "()\n", ))
                elif isinstance(item, NativeExpression):
                    native_expr = item
                    buf.extend(("        _buf.append(to_str(", native_expr.code, "))\n", ))
                else:
                    assert "** unreachable"
        if pos <= i:
            buf.extend(("        _buf.append('''",
                       q(''.join(stmt_list[pos:])),
                       "''')\n", ))


    def expand_init(self, buf, elem_info):
        name = elem_info.name
        buf.extend(("    def init_", name, "(self):\n", ))
        ## text_xxx
        if elem_info.cont_text_p():
            s = elem_info.cont_stmts[0]
            buf.extend(("        self.text_", name, " = '''", q(s), "'''\n", ))
        ## attr_xxx
        buf.extend(('        self.attr_', name, ' = Attribute', ))
        attr_info = elem_info.attr_info
        if attr_info.is_empty():
            buf.append('()\n')
        else:
            buf.append('((\n')
            for space, aname, avalue in attr_info:
                if isinstance(avalue, NativeExpression):
                    s = "'''<"+q(avalue.code)+">'''"
                else:
                    s = repr(avalue)
                buf.extend(("            ('", aname, "',", s, "),\n", ))
            buf.append('        ))\n')


    def expand_elem(self, buf, elem_info):
        name = elem_info.name
        buf.extend((
            '    def elem_', name, '(self):\n'
            '        self.stag_', name, '()\n'
            '        self.cont_', name, '()\n'
            '        self.etag_', name, '()\n'
            ))


    def expand_stag(self, buf, elem_info):
        name = elem_info.name
        stag = elem_info.stag_info
        buf.extend((
            "    def stag_", name, "(self):\n",
            ))
        if stag.tagname:
            buf.extend((
            "        _buf = self._buf\n"
            "        _buf.append('''", stag.head_space or "", "<", stag.tagname, "''')\n"
            "        self.attr_", name, ".append_to(_buf)\n"
            "        _buf.append('''", stag.extra_space or "", stag.is_empty and "/>" or ">", q(stag.tail_space or ""), "''')\n",
            ))
        else:
            s = (stag.head_space or '') + (stag.tail_space or '')
            if s:
                buf.extend(("        self._buf.append('", s, "')\n", ))
            else:
                buf.append("        pass\n")


    def expand_cont(self, buf, elem_info):
        name = elem_info.name
        buf.extend((    '    def cont_', name, '(self):\n', ))
        if elem_info.cont_text_p():
            buf.extend(('        self._buf.append(to_str(self.text_', name, '))\n', ))
        elif elem_info.cont_stmts:
            buf.extend(('        _buf = self._buf\n', ))
            self.expand_items(buf, elem_info.cont_stmts)
        else:
            buf.extend(('        pass\n', ))


    def expand_etag(self, buf, elem_info):
        name = elem_info.name
        etag = elem_info.etag_info
        buf.extend((
            "    def etag_", name, "(self):\n",
            ))
        if not etag:
            buf.extend((
            "        pass\n"
            ))
        elif etag.tagname:
            buf.extend((
            "        _buf = self._buf\n"
            "        _buf.append('''", etag.head_space or "", "</", etag.tagname,
                                 ">", q(etag.tail_space or ""), "''')\n",
            ))
        else:
            s = (etag.head_space or '') + (etag.tail_space or '')
            if s:
                buf.extend(("        self._buf.append('", q(s), "')\n", ))
            else:
                buf.append("        pass\n")



class Main(object):


    def __init__(self, sys_argv=None):
        if sys_argv is None:
            sys_argv = sys.argv[:]
        self.command = os.path.basename(sys_argv[0])
        self.args = sys_argv[1:]


    def execute(self, args=None):
        if args is None:
            args = self.args
        parser = Parser()
        translatr = PythonTranslator()
        for arg in args:
            filename = arg
            parsed_data = parser.parse_file(filename)
            code = translator.translate(parsed_data, filename=filename)
            print code,


if __name__ == '__main__':

    import sys, os
    #input = sys.stdin.read()
    input = """\
<html>
<h1 id="Title">TITLE</h1>
<h2 id="subtitle">SUBTITLE</h2>
<p>hello <span>world</span></p>
<ul id="mark:list">
  <li><span id="mark:item" class="c1">foo</span></li>
</ul>
<dl id="mark:bibliography">
  <dt id="value:item.word">word</dt>
  <dd id="value:item.desc">desc</dd>
</dl>
</html>
"""
    filename = 'template1.html'
    input = open(filename).read()
    parser = TextParser(idflag='all')
    parsed_data = parser.parse(input, filename)
    #print repr(stmt_list)
    #for name, elem_info in parser.elem_info_table.iteritems():
    #    print "%s=%s,%s" % (name, repr(elem_info.stag_info.tag_text), repr(elem_info.etag_info.tag_text))
    translator = PythonTranslator()
    code = translator.translate(parsed_data)
    print code,
