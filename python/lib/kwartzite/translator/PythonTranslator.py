###
### $Rev$
### $Release$
### $Copyright$
###


import os, re
#import kwartzite.config as config
from kwartzite.config import PythonTranslatorConfig
from kwartzite.util import quote, define_properties
from kwartzite.parser.TextParser import ElementInfo, Expression
from kwartzite.translator import Translator



def q(string):
    s = quote(string)
    if s.endswith("\r\n"):
        return s[0:-2] + "\\r\\n"
    if s.endswith("\n"):
        return s[0:-1] + "\\n"
    return s



class PythonTranslator(Translator, PythonTranslatorConfig):


    _property_descriptions = (
        ('classname' , 'str'  , 'classname pattern'),
        ('baseclass' , 'str'  , 'parent class name'),
        ('encoding'  , 'str'  , 'encoding name'),
        ('mainprog'  , 'bool' , 'define main program or not'),
        ('context'   , 'bool' , 'use context object in constructor or not'),
        ('nullobj'   , 'bool' , 'use NULL object instead of None'),
        ('fragment'  , 'bool' , 'define element_xxx() and content_xxx()'),
        ('attrobj'   , 'bool' , 'use kwartzite.attribute.Attribute instead of dict'),
        ('accessors' , 'bool' , 'define set_{text|attr|node}_xxx() or not'),
    )
    define_properties(_property_descriptions, baseclass='object', context=True)


    def __init__(self, classname=None, baseclass=None, encoding=None, mainprog=None, context=None, nullobj=None, fragment=None, attrobj=None, accessors=None, **properties):
        Translator.__init__(self, **properties)
        if classname   is not None:  self.CLASSNAME = classname
        if baseclass   is not None:  self.BASECLASS = baseclass
        if encoding    is not None:  self.ENCODING  = encoding
        if mainprog    is not None:  self.MAINPROG  = mainprog
        if context     is not None:  self.CONTEXT   = context
        if nullobj     is not None:  self.NULLOBJ   = nullobj
        if fragment    is not None:  self.FRAGMENT  = fragment
        if attrobj     is not None:  self.ATTROBJ   = attrobj
        if accessors   is not None:  self.ACCESSORS = accessors
        self.nullvalue = nullobj and 'NULL' or 'None'


    def translate(self, template_info, **properties):
        stmt_list  = template_info.stmt_list
        elem_table = template_info.elem_table
        filename   = properties.get('filename') or template_info.filename
        classname  = properties.get('classname') or self.CLASSNAME
        classname = self.build_classname(filename, pattern=classname, **properties)
        buf = []
        extend = buf.extend
        #
        if self.ENCODING:
            extend(('# -*- coding: ', self.ENCODING, " -*-\n", ))
        if filename:
            extend(('## generated from ', filename, '\n', ))
        buf.append('\n')
        #
        if self.ATTROBJ:
            extend(('from kwartzite.attribute import Attribute\n', ))
        if self.ENCODING:
            extend(('from kwartzite.util import escape_xml, generate_tostrfunc\n'
                    'to_str = generate_tostrfunc(', repr(self.ENCODING), ')\n', ))
        else:
            extend(('from kwartzite.util import escape_xml, to_str\n', ))
        if self.NULLOBJ:
            extend(('from kwartzite.util import ', self.nullvalue, '\n', ))
        s = self.NULLOBJ and ", 'NULL'" or ''
        extend((    'h = escape_xml\n'
                    "__all__ = ['", classname, "', 'escape_xml', 'to_str', 'h'", s, "]\n"
                    '\n'
                    ,))
        #
        extend((    '\n'
                    'class ', classname, '(', self.BASECLASS, '):\n'
                    '\n'
                    ,))
        if self.CONTEXT:
            extend(('    def __init__(self, **_context):\n'
                    '        for k, v in _context.iteritems():\n'
                    '            setattr(self, k, v)\n'
                    '        self._context = _context\n'
                    ,))
        else:
            extend(('    def __init__(self):\n'
                    ,))
        #extend((    '        self._set_buf([])\n'
        #            ,))
        for name, elem in elem_table.iteritems():
            #extend(('        self.init_', name, '()\n', ))
            directive = elem.directive
            if directive.name in ('mark', 'attr', 'textattr'):
                extend((
                    '        self.attr_', name, ' = self.attr_', name, '.copy()\n'
                    ,))
        buf.append( '\n'
                    '    _init__ = __init__\n'
                    '\n')
        #
        self.expand_utils(buf, elem)
        #
        extend((    '    def setup(self)\n'
                    '        pass\n'
                    '\n'
                    ,))
        extend((    '    def create_document(self):\n'
                    '        self.setup()\n'
                    '        buf = []\n'
                    '        self.append_document(buf)\n'
                    '        return \'\'.join(buf)\n'
                    '\n'
                    '    _create_document = create_document\n'
                    '\n'
                    ,))
        extend((    '    def append_document(self, buf):\n'
                    '        self._set_buf(buf)\n'
                    '        _append = self._append\n'
                    '        _extend = self._extend\n'
                    ,))
        self.expand_stmt_list(buf, stmt_list)
        extend((    '\n'
                    '    _append_document = append_document\n'
                    '\n'
                    ,))
        #
        for name, elem in elem_table.iteritems():
            extend(("\n"
                    "    ## element '", name, "'\n"
                    "\n"
                    ,))
            if elem.directive.name == 'mark':
                self.expand_init(buf, elem); buf.append("\n")
                self.expand_elem(buf, elem); buf.append("\n")
                self.expand_stag(buf, elem); buf.append("\n")
                self.expand_cont(buf, elem); buf.append("\n")
                self.expand_etag(buf, elem); buf.append("\n")
                self.expand_aliases(buf, elem); buf.append("\n")
                if self.FRAGMENT:
                    self.expand_create_element(buf, elem); buf.append("\n")
                    self.expand_create_content(buf, elem); buf.append("\n")
            else:
                self.expand_init(buf, elem); buf.append("\n")
                extend((
                    "    _init_", name, " = init_", name, "\n"
                    "\n"
                    ,))
            if self.ACCESSORS:
                self.expand_accessors(buf, elem)
        #extend((
        #    "\n"
        #    "class ", classname, "(", classname, "_):\n"
        #    "    pass\n"
        #    "\n",
        #    ))
        #
        if self.MAINPROG:
            extend(("\n"
                    "# for test\n"
                    "if __name__ == '__main__':\n"
                    "    print ", classname, "().create_document(),\n"
                    "\n"
                    ,))
        return ''.join(buf)


    def expand_stmt_list(self, buf, stmt_list):
        def flush(L, buf):
            if not L:
                return
            elif len(L) == 1:
                buf.extend(("        _append(", L[0][:-2], ")\n", ))
            else:
                if L[-1].endswith('\n'):
                    L[-1] = L[-1][:-1] + ' '
                buf.append("        _extend((")
                buf.extend(L)
                buf.append("))\n")
            L[:] = ()
        L = []
        extend = buf.extend
        for item in stmt_list:
            if isinstance(item, (str, unicode)):
                s = item.endswith('\n') and '\n' or ' '
                L.append("'''" + q(item) + "'''," + s)
            elif isinstance(item, ElementInfo):
                flush(L, buf)
                elem = item
                assert elem.directive.name == 'mark'
                extend(("        self.elem_", elem.name, "()\n", ))
            elif isinstance(item, Expression):
                expr = item
                kind = expr.kind
                if   kind == 'text':
                    L.append("to_str(self.text_" + expr.name + "), ")
                elif kind == 'attr':
                    flush(L, buf)
                    self.expand_attr(buf, expr.name)
                elif kind == 'node':
                    L.append("to_str(self.node_" + expr.name + "), ")
                elif kind == 'native':
                    L.append("to_str(" + expr.code + "), ")
                else:
                    assert "** unreachable"
            else:
                assert "** unreachable"
        flush(L, buf)


    def expand_attr(self, buf, name):
        extend = buf.extend
        s = self.NULLOBJ and (", "+self.nullvalue) or ""
        if self.ATTROBJ:
            extend((
            "        self.attr_", name, ".append_to(self._buf", s, ")\n"
            ,))
        else:
            extend((
            "        self._append_attr(self.attr_", name, s, ")\n"
            #"        for k, v in self.attr_", name, ".iteritems():\n"
            #"            if v is not ", self.nullvalue, ": self._extend((' ', k, '=\"', v, '\"'))\n"
            ,))


    def expand_init(self, buf, elem):
        name = elem.name
        extend = buf.extend
        d_name = elem.directive.name
        #extend(("    def init_", name, "(self):\n", ))
        ## node_xxx
        if d_name in ('mark', 'node'):
            #extend(("        self.node_", name, " = ", self.nullvalue, "\n", ))
            extend(("    node_", name, " = ", self.nullvalue, "\n", ))
        ## text_xxx
        if d_name in ('mark', 'text', 'textattr'):
            if elem.cont_text_p():
                s = elem.cont[0]
                #extend(("        self.text_", name, " = '''", q(s), "'''\n", ))
                extend(("    text_", name, " = '''", q(s), "'''\n", ))
            else:
                #extend(("        self.text_", name, " = ", self.nullvalue, "\n", ))
                extend(("    text_", name, " = ", self.nullvalue, "\n", ))
        ## attr_xxx
        if d_name not in ('mark', 'attr', 'textattr'):
            pass
        elif not self.ATTROBJ:
            #extend(('        self.attr_', name, ' = ', ))
            extend(('    attr_', name, ' = ', ))
            attr = elem.attr
            if attr.is_empty():
                buf.append('{}\n')
            else:
                buf.append('{\n')
                for space, aname, avalue in attr:
                    #extend(("            '", q(aname), "':'", q(avalue), "',\n", ))
                    extend(("        '", q(aname), "':'", q(avalue), "',\n", ))
                #buf.append('        }\n')
                buf.append('    }\n')
        else:
            #extend(('        self.attr_', name, ' = Attribute', ))
            extend(('    attr_', name, ' = Attribute', ))
            attr = elem.attr
            if attr.is_empty():
                buf.append('()\n')
            else:
                buf.append('((\n')
                for space, aname, avalue in attr:
                    #if isinstance(avalue, Expression):
                    #    s = "'''<"+q(avalue.code)+">'''"
                    #else:
                    #    s = repr(avalue)
                    #s = "'" + q(avalue) + "'"
                    #extend(("            ('", aname, "','", q(avalue), "',", repr(space), "),\n", ))
                    extend(("        ('", aname, "','", q(avalue), "',", repr(space), "),\n", ))
                #buf.append('        ))\n')
                buf.append('    ))\n')


    def expand_elem(self, buf, elem):
        name = elem.name
        buf.extend((
            '    def elem_', name, '(self):\n'
            '        if self.node_', name, ' is ', self.nullvalue, ':\n'
            '            self.stag_', name, '()\n'
            '            self.cont_', name, '()\n'
            '            self.etag_', name, '()\n'
            '        else:\n'
            '            self._append(to_str(self.node_', name, '))\n'
            ,))


    def expand_stag(self, buf, elem):
        name = elem.name
        extend = buf.extend
        stag = elem.stag
        extend((
            "    def stag_", name, "(self):\n"
            ,))
        if stag.name:
            s = self.NULLOBJ and (", "+self.nullvalue) or ""
            extend((
            "        _append = self._append\n"
            "        _append('''", stag.head_space or "", "<", stag.name, "''')\n"
            ,))
            self.expand_attr(buf, name)
            extend((
            "        _append('''", stag.extra_space or "", stag.is_empty and "/>" or ">", q(stag.tail_space or ""), "''')\n"
            ,))
        else:
            s = (stag.head_space or '') + (stag.tail_space or '')
            if s:
                extend(("        self._append('", s, "')\n", ))
            else:
                extend(("        pass\n", ))


    def expand_cont(self, buf, elem):
        name = elem.name
        extend = buf.extend
        extend((    '    def cont_', name, '(self):\n', ))
        if elem.cont_text_p():
            extend(('        self._append(to_str(self.text_', name, '))\n', ))
        else:
            extend(('        _append = self._append\n', ))
            extend(('        _extend = self._extend\n', ))
            extend(('        if self.text_', name, ' is not ', self.nullvalue, ':\n'
                    '            _append(self.text_', name, ')\n', ))
            if not elem.cont:
                return
            extend(('            return\n', ))
            self.expand_stmt_list(buf, elem.cont)


    def expand_etag(self, buf, elem):
        name = elem.name
        extend = buf.extend
        etag = elem.etag
        extend((
            "    def etag_", name, "(self):\n"
            ,))
        if not etag:
            extend((
            "        pass\n"
            ,))
        elif etag.name:
            extend((
            "        self._append('''", etag.head_space or "", "</", etag.name,
                                 ">", q(etag.tail_space or ""), "''')\n"
            ,))
        else:
            s = (etag.head_space or '') + (etag.tail_space or '')
            if s:
                extend((
            "        self._append('", q(s), "')\n"
            ,))
            else:
                extend((
            "        pass\n"
            ,))


    def expand_aliases(self, buf, elem):
        extend = buf.extend
        name = elem.name
        extend((
            #"    _init_", name, " = init_", name, "\n"
            "    _elem_", name, " = elem_", name, "\n"
            "    _stag_", name, " = stag_", name, "\n"
            "    _cont_", name, " = cont_", name, "\n"
            "    _etag_", name, " = etag_", name, "\n"
            "\n"
            ,))


    def expand_create_element(self, buf, elem):
        self._expand_create_element_or_content(buf, elem, 'element')


    def expand_create_content(self, buf, elem):
        self._expand_create_element_or_content(buf, elem, 'content')


    def _expand_create_element_or_content(self, buf, elem, kind):
        s1, s2 = kind == 'element' and ('element', 'elem') or ('content', 'cont')
        name = elem.name
        extend = buf.extend
        extend((
            "    def create_", s1, "_", name, "(self, _buf=None):\n"
            "        if _buf is None: self._set_buf([])\n"
            "        else:            self._set_buf(_buf)\n"
            "        self.", s2, "_", name, "()\n"
            "        if _buf is None: return ''.join(self._buf)\n"
            "        else:            return None\n"
            ,))


    def expand_accessors(self, buf, elem):
        extend = buf.extend
        name = elem.name
        d_name = elem.directive.name
        if d_name in ('mark', 'text', 'textattr', ):
            extend((
            "    def set_text_", name, "(self, value):\n"
            "        self.text_", name, " = escape_xml(to_str(value))\n"
            "\n", ))
        if d_name in ('mark', ):
            extend((
            "    def set_node_", name, "(self, value):\n"
            "        self.node_", name, " = escape_xml(to_str(value))\n"
            "\n", ))
        if d_name in ('mark', 'attr', 'textattr', ):
            extend((
            "    def set_attr_", name, "(self, name, value):\n"
            "        if value is ", self.nullvalue, ":\n"
            "            self.attr_", name, "[name] = ", self.nullvalue, "\n"
            "        else:\n"
            "            self.attr_", name, "[name] = escape_xml(to_str(value))\n"
            "\n"
            "    def del_attr_", name, "(self, name):\n"
            "        self.attr_", name, ".pop(name, None)\n"
            "\n", ))


    def expand_utils(self, buf, elem):
        extend = buf.extend
        extend((    '    def _set_buf(self, _buf):\n'
                    '        self._buf = _buf\n'
                    '        self._append = _buf.append\n'
                    '        self._extend = _buf.extend\n'
                    '\n'
                    ,))
        #
        extend((    '    def echo(self, value):\n'
                    '        self._append(to_str(value))\n'
                    '\n'
                    ,))
        #
        if not self.ATTROBJ:
            extend(('    def _append_attr(self, attr, nullvalue=None):\n'
                    '        _extend = self.extend\n'
                    '        for k, v in attr.iteritems():\n'
                    '            if v is not nullvalue:\n'
                    '                _extend((\' \', k, \'="\', v, \'"\'))\n'
                    '\n'
                    ,))
