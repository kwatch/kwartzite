###
### $Rev$
### $Release$
### $Copyright$
###


import os, re
#import config
from kwartzite.util import quote
from kwartzite.parser.TextParser import ElementInfo, Expression
from kwartzite.translator import Translator



def q(string):
    s = quote(string)
    if s.endswith("\r\n"):
        return s[0:-2] + "\\r\\n"
    if s.endswith("\n"):
        return s[0:-1] + "\\n"
    return s



class PythonTranslator(Translator):


    def translate(self, template_info, filename=None, classname=None, baseclass=None, encoding=None, mainprog=None, context=None, nullobj=None, **kwargs):
        propget = self.properties.get
        if filename    is None:  filename  = template_info.filename
        if classname   is None:  classname = propget('classname')
        if baseclass   is None:  baseclass = propget('baseclass', 'object')
        if encoding    is None:  encoding  = self.encoding
        if mainprog    is None:  mainprog  = propget('mainprog', True)
        if context     is None:  context   = propget('context', True)
        if nullobj     is None:  nullobj   = propget('nullobj', False)
        self.nullobj = nullobj
        self.nullvalue = nullobj and 'NULL' or 'None'
        return self.generate_code(template_info, filename=filename, classname=classname, baseclass=baseclass, encoding=encoding, mainprog=mainprog, context=context, nullobj=nullobj, **kwargs)


    def generate_code(self, template_info, filename=None, classname=None, baseclass=None, encoding=None, mainprog=None, context=None, nullobj=None, **properties):
        stmt_list  = template_info.stmt_list
        elem_table = template_info.elem_table
        classname = self.build_classname(filename, pattern=classname, **properties)
        buf = []
        extend = buf.extend
        if encoding:
            extend(('# -*- coding: ', encoding, " -*-\n", ))
        if filename:
            extend(('## generated from ', filename, '\n', ))
        extend((
            '\n'
            'from kwartzite.attribute import Attribute\n',
            ))
        if encoding:
            extend((
            'from kwartzite.util import escape_xml, generate_tostrfunc\n'
            'to_str = generate_tostrfunc(', repr(encoding), ')\n'
            ))
        else:
            extend((
            'from kwartzite.util import escape_xml, to_str\n'
            ))
        if self.nullobj:
            extend((
            'from kwartzite.util import ', self.nullvalue, '\n'
            ))
        extend((
            'h = escape_xml\n'
            "__all__ = ['", classname, "', 'escape_xml', 'to_str', 'h', ]\n"
            '\n'
            '\n'
            'class ', classname, '(', baseclass, '):\n'
            '\n'
            ))
        if context:
            extend((
            '    def __init__(self, **_context):\n'
            '        for k, v in _context.iteritems():\n'
            '            setattr(self, k, v)\n'
            '        self._context = _context\n'
            '        self._buf = []\n'
            ))
        else:
            extend((
            '    def __init__(self):\n'
            '        self._buf = []\n'
            ))
        for name, elem in elem_table.iteritems():
            extend(('        self.init_', name, '()\n', ))
        extend((
            '\n'
            '    def create_document(self):\n'
            '        _buf = self._buf\n'
            ))
        self.expand_items(buf, stmt_list)
        extend((
            "        return ''.join(_buf)\n"
            "\n",
            ))
        for name, elem in elem_table.iteritems():
            extend((
            "\n"
            "    ## element '", name, "'\n"
            "\n"
            ))
            self.expand_init(buf, elem); buf.append("\n")
            if elem.directive.name == 'mark':
                self.expand_elem(buf, elem); buf.append("\n")
                self.expand_stag(buf, elem); buf.append("\n")
                self.expand_cont(buf, elem); buf.append("\n")
                self.expand_etag(buf, elem); buf.append("\n")
            if elem.directive.name == 'mark':
                extend((
            "    _init_", name, " = init_", name, "\n"
            "    _elem_", name, " = elem_", name, "\n"
            "    _stag_", name, " = stag_", name, "\n"
            "    _cont_", name, " = cont_", name, "\n"
            "    _etag_", name, " = etag_", name, "\n"
                ))
            else:
                extend((
            "    _init_", name, " = init_", name, "\n"
                ))
            buf.append("\n")
        #extend((
        #    "\n"
        #    "class ", classname, "(", classname, "_):\n"
        #    "    pass\n"
        #    "\n",
        #    ))
        if mainprog:
            extend((
            "\n"
            "# for test\n"
            "if __name__ == '__main__':\n"
            "    print ", classname, "().create_document(),\n"
            "\n"
            ))
        return ''.join(buf)


    def expand_items(self, buf, stmt_list):
        def flush(L, buf):
            if not L:
                return
            elif len(L) == 1:
                buf.extend(("        _buf.append(", L[0][:-2], ")\n", ))
            else:
                if L[-1].endswith('\n'):
                    L[-1] = L[-1][:-1] + ' '
                buf.append("        _buf.extend((")
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
                    s = self.nullobj and (", "+self.nullvalue) or ""
                    extend(("        self.attr_", expr.name, ".append_to(self._buf", s, ")\n", ))
                elif kind == 'node':
                    L.append("to_str(self.node_" + expr.name + "), ")
                elif kind == 'native':
                    L.append("to_str(" + expr.code + "), ")
                else:
                    assert "** unreachable"
            else:
                assert "** unreachable"
        flush(L, buf)


    def expand_init(self, buf, elem):
        name = elem.name
        extend = buf.extend
        d_name = elem.directive.name
        extend(("    def init_", name, "(self):\n", ))
        ## node_xxx
        if d_name in ('mark', 'node'):
            extend(("        self.node_", name, " = ", self.nullvalue, "\n", ))
        ## text_xxx
        if d_name in ('mark', 'text', 'textattr'):
            if elem.cont_text_p():
                s = elem.cont[0]
                extend(("        self.text_", name, " = '''", q(s), "'''\n", ))
            else:
                extend(("        self.text_", name, " = ", self.nullvalue, "\n", ))
        ## attr_xxx
        if d_name in ('mark', 'attr', 'textattr'):
            extend(('        self.attr_', name, ' = Attribute', ))
            attr = elem.attr
            if attr.is_empty():
                buf.append('()\n')
            else:
                buf.append('((\n')
                for space, aname, avalue in attr:
                    if isinstance(avalue, Expression):
                        s = "'''<"+q(avalue.code)+">'''"
                    else:
                        s = repr(avalue)
                    extend(("            ('", aname, "',", s, "),\n", ))
                buf.append('        ))\n')


    def expand_elem(self, buf, elem):
        name = elem.name
        buf.extend((
            '    def elem_', name, '(self):\n'
            '        if self.node_', name, ' is ', self.nullvalue, ':\n'
            '            self.stag_', name, '()\n'
            '            self.cont_', name, '()\n'
            '            self.etag_', name, '()\n'
            '        else:\n'
            '            self._buf.append(to_str(self.node_', name, '))\n'
            ))


    def expand_stag(self, buf, elem):
        name = elem.name
        extend = buf.extend
        stag = elem.stag
        extend((
            "    def stag_", name, "(self):\n",
            ))
        if stag.name:
            s = self.nullobj and (", "+self.nullvalue) or ""
            extend((
            "        _buf = self._buf\n"
            "        _buf.append('''", stag.head_space or "", "<", stag.name, "''')\n"
            "        self.attr_", name, ".append_to(_buf", s, ")\n"
            "        _buf.append('''", stag.extra_space or "", stag.is_empty and "/>" or ">", q(stag.tail_space or ""), "''')\n",
            ))
        else:
            s = (stag.head_space or '') + (stag.tail_space or '')
            if s:
                extend(("        self._buf.append('", s, "')\n", ))
            else:
                extend(("        pass\n", ))


    def expand_cont(self, buf, elem):
        name = elem.name
        extend = buf.extend
        extend((    '    def cont_', name, '(self):\n', ))
        if elem.cont_text_p():
            extend(('        self._buf.append(to_str(self.text_', name, '))\n', ))
        else:
            extend(('        _buf = self._buf\n', ))
            extend(('        if self.text_', name, ' is not ', self.nullvalue, ':\n'
                    '            _buf.append(self.text_', name, ')\n', ))
            if not elem.cont:
                return
            extend(('            return\n', ))
            self.expand_items(buf, elem.cont)


    def expand_etag(self, buf, elem):
        name = elem.name
        extend = buf.extend
        etag = elem.etag
        extend((
            "    def etag_", name, "(self):\n",
            ))
        if not etag:
            extend((
            "        pass\n"
            ))
        elif etag.name:
            extend((
            "        _buf = self._buf\n"
            "        _buf.append('''", etag.head_space or "", "</", etag.name,
                                 ">", q(etag.tail_space or ""), "''')\n",
            ))
        else:
            s = (etag.head_space or '') + (etag.tail_space or '')
            if s:
                extend((
            "        self._buf.append('", q(s), "')\n",
            ))
            else:
                extend((
            "        pass\n",
            ))
