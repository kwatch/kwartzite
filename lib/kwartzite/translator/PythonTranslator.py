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


    def translate(self, template_info, filename=None, classname=None, baseclass=None, encoding=None, mainprog=None, **kwargs):
        if filename is None:
            filename = template_info.filename
        if classname is None:
            classname = self.build_classname(filename, **kwargs)
        if baseclass is None:
            baseclass = self.properties.get('baseclass', 'object')
        if encoding is None:
            encoding = self.encoding
        if mainprog is None:
            mainprog = self.properties.get('mainprog', True)
        return self.generate_code(template_info, filename=filename, classname=classname, baseclass=baseclass, encoding=encoding, mainprog=mainprog, **kwargs)


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


    def generate_code(self, template_info, filename=None, classname=None, baseclass=None, encoding=None, mainprog=None, **properties):
        stmt_list       = template_info.stmt_list
        elem_info_table = template_info.elem_info_table
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
            'from kwartzite.util import escape_xml, generate_tostrfunc, NULL\n'
            'to_str = generate_tostrfunc(', repr(encoding), ')\n'
            ))
        else:
            buf.extend((
            'from kwartzite.util import escape_xml, to_str, NULL\n'
            ))
        buf.extend((
            'h = escape_xml\n'
            "__all__ = ['", classname, "', 'escape_xml', 'to_str', 'h', ]\n"
            '\n'
            '\n'
            'class ', classname, '(', baseclass, '):\n'
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
            buf.extend((
            "\n"
            "    ## element '", name, "'\n"
            "\n"
            ))
            self.expand_init(buf, elem_info); buf.append("\n")
            if elem_info.directive.name == 'mark':
                self.expand_elem(buf, elem_info); buf.append("\n")
                self.expand_stag(buf, elem_info); buf.append("\n")
                self.expand_cont(buf, elem_info); buf.append("\n")
                self.expand_etag(buf, elem_info); buf.append("\n")
            if elem_info.directive.name == 'mark':
                buf.extend((
            "    _init_", name, " = init_", name, "\n"
            "    _elem_", name, " = elem_", name, "\n"
            "    _stag_", name, " = stag_", name, "\n"
            "    _cont_", name, " = cont_", name, "\n"
            "    _etag_", name, " = etag_", name, "\n"
                ))
            else:
                buf.extend((
            "    _init_", name, " = init_", name, "\n"
                ))
            buf.append("\n")
        #buf.extend((
        #    "\n"
        #    "class ", classname, "(", classname, "_):\n"
        #    "    pass\n"
        #    "\n",
        #    ))
        if mainprog:
            buf.extend((
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
        for item in stmt_list:
            if isinstance(item, (str, unicode)):
                s = item.endswith('\n') and '\n' or ' '
                L.append("'''" + q(item) + "'''," + s)
            elif isinstance(item, ElementInfo):
                flush(L, buf)
                elem_info = item
                assert elem_info.directive.name == 'mark'
                buf.extend(("        self.elem_", elem_info.name, "()\n", ))
            elif isinstance(item, Expression):
                expr = item
                kind = expr.kind
                if   kind == 'text':
                    L.append("to_str(self.text_" + expr.name + "), ")
                elif kind == 'attr':
                    flush(L, buf)
                    buf.extend(("        self.attr_", expr.name, ".append_to(self._buf)\n", ))
                elif kind == 'node':
                    L.append("to_str(self.node_" + expr.name + "), ")
                elif kind == 'native':
                    L.append("to_str(" + expr.code + "), ")
                else:
                    assert "** unreachable"
            else:
                assert "** unreachable"
        flush(L, buf)


    def expand_init(self, buf, elem_info):
        name = elem_info.name
        d_name = elem_info.directive.name
        buf.extend(("    def init_", name, "(self):\n", ))
        ## node_xxx
        if d_name in ('mark', 'node'):
            buf.extend(("        self.node_", name, " = NULL\n", ))
        ## text_xxx
        if d_name in ('mark', 'text', 'textattr'):
            if elem_info.cont_text_p():
                s = elem_info.cont_stmts[0]
                buf.extend(("        self.text_", name, " = '''", q(s), "'''\n", ))
            else:
                buf.extend(("        self.text_", name, " = NULL\n", ))
        ## attr_xxx
        if d_name in ('mark', 'attr', 'textattr'):
            buf.extend(('        self.attr_', name, ' = Attribute', ))
            attr_info = elem_info.attr_info
            if attr_info.is_empty():
                buf.append('()\n')
            else:
                buf.append('((\n')
                for space, aname, avalue in attr_info:
                    if isinstance(avalue, Expression):
                        s = "'''<"+q(avalue.code)+">'''"
                    else:
                        s = repr(avalue)
                    buf.extend(("            ('", aname, "',", s, "),\n", ))
                buf.append('        ))\n')


    def expand_elem(self, buf, elem_info):
        name = elem_info.name
        buf.extend((
            '    def elem_', name, '(self):\n'
            '        if self.node_', name, ' is NULL:\n'
            '            self.stag_', name, '()\n'
            '            self.cont_', name, '()\n'
            '            self.etag_', name, '()\n'
            '        else:\n'
            '            self._buf.append(to_str(self.node_', name, '))\n'
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
        else:
            buf.extend(('        _buf = self._buf\n', ))
            buf.extend(('        if self.text_', name, ' is not NULL:\n'
                        '            _buf.append(self.text_', name, ')\n', ))
            if not elem_info.cont_stmts:
                return
            buf.append( '            return\n')
            self.expand_items(buf, elem_info.cont_stmts)


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
