###
### $Rev$
### $Release$
### $Copyright$
###


import os, re
#import config
from kwartzite.util import qquote
from kwartzite.parser.TextParser import ElementInfo, Expression
from kwartzite.translator import Translator



def q(string):
    s = qquote(string)
    L = []
    for line in s.splitlines(True):
        if line.endswith("\r\n"):  line = line[0:-2] + "\\r\\n"
        elif line.endswith("\n"):  line = line[0:-1] + "\\n"
        L.append(line)
    return '"\n            + "'.join(L)



def c(name):
    #return ''.join([ s.capitalize() for s in name.split('_') ])
    return name.title().replace('_', '')



class JavaTranslator(Translator):


    def translate(self, template_info, filename=None, classname=None, baseclass=None, encoding=None, mainprog=None, package=None, interface=None, context=None, nullobj=None, **kwargs):
        propget = self.properties.get
        if filename    is None:  filename    = template_info.filename
        if classname   is None:  classname   = propget('classname')
        if baseclass   is None:  baseclass   = propget('baseclass', 'Object')
        if encoding    is None:  encoding    = self.encoding
        if mainprog    is None:  mainprog    = propget('mainprog', True)
        if package     is None:  package     = propget('package')
        if interface   is None:  interface   = propget('interface')
        if context     is None:  context     = propget('context', False)
        if nullobj     is None:  nullobj     = propget('nullobj', False)
        self.nullobj = nullobj
        self.nullvalue = nullobj and 'NULL' or 'null'
        return self.generate_code(template_info, filename=filename, classname=classname, baseclass=baseclass, encoding=encoding, mainprog=mainprog, package=package, interface=interface, context=context, nullobj=nullobj, **kwargs)


    def generate_code(self, template_info, filename=None, classname=None, baseclass=None, encoding=None, mainprog=None, package=None, interface=None, context=None, nullobj=None, **properties):
        stmt_list       = template_info.stmt_list
        elem_info_table = template_info.elem_info_table
        classname = self.build_classname(filename, pattern=classname, **properties)
        buf = []
        extend = buf.extend
        if filename:
            extend((
            '// generated from ', filename, '\n'
            '\n'
            ))
        if package:
            extend((
            'package ', package, ';\n'
            '\n'
            ))
        s = interface and ' implements ' + interface or ''
        extend((
            'import java.util.Map;\n'
            'import java.util.HashMap;\n'
            'import java.util.Iterator;\n'
            '\n'
            '\n'
            'public class ', classname, ' extends ', baseclass, s, ' {\n'
            '\n'
            '    protected StringBuffer _buf = new StringBuffer();\n'
            ))
        if context:
            extend((
            '    protected Map _context;\n'
            '\n'
            '    public ', classname, '() {\n'
            '         this(new HashMap());\n'
            '    }\n'
            '\n'
            '    public ', classname, '(Map _context) {\n'
            '        this._context = _context;\n'
            ))
        else:
            extend((
            '\n'
            '    public ', classname, '() {\n'
            ))
        for name, elem_info in elem_info_table.iteritems():
            extend(('        init', c(name), '();\n', ))
        extend((
            '    }\n'
            '\n',
            ))
        self.expand_utils(buf)
        extend((
            '\n'
            '    public String createDocument() {\n',
            ))
        self.expand_items(buf, stmt_list)
        extend((
            '        return _buf.toString();\n'
            '    }\n'
            '\n',
            ))
        for name, elem_info in elem_info_table.iteritems():
            extend((
            '\n'
            '    // element \'', name, '\'\n'
            '\n'
            ))
            self.expand_init(buf, elem_info); buf.append("\n")
            if elem_info.directive.name != 'mark':  continue
            self.expand_elem(buf, elem_info); buf.append("\n")
            self.expand_stag(buf, elem_info); buf.append("\n")
            self.expand_cont(buf, elem_info); buf.append("\n")
            self.expand_etag(buf, elem_info); buf.append("\n")
        if mainprog:
            extend((
            '\n'
            '    // for test\n'
            '    public static void main(String[] args) {\n'
            '        System.out.print(new ', classname, '().createDocument());\n'
            '    }\n'
            ))
        buf.append(
            '\n'
            '}\n'
            )
        return ''.join(buf)


    def expand_utils(self, buf):
        if self.nullobj:
            buf.extend((
            '\n'
            '    //public static final Object ', self.nullvalue, ' = new Object();\n'
            '    public static final String ', self.nullvalue, ' = new String("");\n'
            ))
        buf.extend((
            '\n'
            '    public static String toStr(Object val) {\n'
            '        return val == null ? "" : val.toString();\n'
            '    }\n'
            '\n'
            '    public static String toStr(String val) {\n'
            '        return val == null ? "" : val;\n'
            '    }\n'
            '\n'
            '    public void appendAttribute(Map attr) {\n'
            '        for (Iterator it = attr.keySet().iterator(); it.hasNext(); ) {\n'
            '            Object key = it.next();\n'
            '            Object val = attr.get(key);\n'
            '            if (val != ', self.nullvalue, ') {\n'
            '                _buf.append(\' \').append(key).append("=\\"").append(toStr(val)).append(\'"\');\n'
            #'                _buf.append(\' \').append(key).append("=\\"").append(val).append(\'"\');\n'
            '            }\n'
            '        }\n'
            '    }\n'
            ))


    def expand_items(self, buf, stmt_list):
        def flush(L, buf):
            if L:
                buf.append('        _buf')
                for s in L:
                    buf.extend(('.append(', s, ')', ))
                buf.append(';\n')
                L[:] = ()
        L = []
        for item in stmt_list:
            if isinstance(item, (str, unicode)):
                #s = item.endswith('\n') and '\n            ' or ''
                s = ''
                L.append('"' + q(item) + '"' + s)
            elif isinstance(item, ElementInfo):
                flush(L, buf)
                elem_info = item
                assert elem_info.directive.name == 'mark'
                buf.extend(("        elem", c(elem_info.name), "();\n", ))
            elif isinstance(item, Expression):
                expr = item
                kind = expr.kind
                if   kind == 'text':
                    L.append("toStr(text" + c(expr.name) + ")")
                elif kind == 'attr':
                    flush(L, buf)
                    buf.extend(("        appendAttribute(attr", c(expr.name), ");\n", ))
                elif kind == 'node':
                    L.append("toStr(self.node" + c(expr.name) + ")")
                elif kind == 'native':
                    L.append("toStr(" + expr.code + ")")
                else:
                    assert "** unreachable"
            else:
                assert "** unreachable"
        flush(L, buf)


    def expand_init(self, buf, elem_info):
        name = elem_info.name
        extend = buf.extend
        ## instance variable declaration
        initval = not elem_info.cont_text_p() and (' = '+self.nullvalue) or ''
        d_name = elem_info.directive.name
        if d_name in ('mark', 'attr', 'textattr'):
            extend(('    public Map attr', c(name), ';\n', ))
        if d_name in ('mark', 'text', 'textattr'):
            extend(('    public String text', c(name), initval, ';\n', ))
        if d_name in ('mark', 'node'):
            extend(('    public String node', c(name), ' = ', self.nullvalue, ';\n', ))
        ## start of init_xxx
        extend((
            '\n'
            '    public void init', c(name), '() {\n'
            ))
        ## attr_xxx
        if d_name in ('mark', 'attr', 'textattr'):
            extend((
                '        attr', c(name), ' = new HashMap();\n'
                ))
            for space, aname, avalue in elem_info.attr_info:
                if isinstance(avalue, Expression):
                    s = avalue.code;
                else:
                    s = '"' + q(avalue) + '"'
                extend((
                '        attr', c(name), '.put("', aname, '", ', s, ');\n',
                ))
        ## text_xxx
        if d_name in ('mark', 'text', 'textattr'):
            if elem_info.cont_text_p():
                assert len(elem_info.cont_stmts) == 1
                extend((
                '        text', c(name), ' = "', q(elem_info.cont_stmts[0]), '";\n'
                ))
        ## end of init_xxx
        extend((
            '    }\n',
            ))


    def expand_elem(self, buf, elem_info):
        name = elem_info.name
        buf.extend((
            '    public void elem', c(name), '() {\n'
            '        if (node', c(name), ' == ', self.nullvalue, ') {\n'
            '            stag', c(name), '();\n'
            '            cont', c(name), '();\n'
            '            etag', c(name), '();\n'
            '        } else {\n'
            '            _buf.append(toStr(node', c(name), '));\n'
            '        }\n'
            '    }\n'
            ))


    def expand_stag(self, buf, elem_info):
        name = elem_info.name
        extend = buf.extend
        stag = elem_info.stag_info
        extend((
            '    public void stag', c(name), '() {\n'
            ))
        if stag.tagname:
            extend((
            '        _buf.append("', stag.head_space or '', '<', stag.tagname, '");\n'
            '        appendAttribute(attr', c(name), ');\n'
            '        _buf.append("', q(stag.extra_space or ''), stag.is_empty and ' />' or '>', q(stag.tail_space or ''), '");\n',
            ))
        else:
            s = (stag.head_space or '') + (stag.tail_space or '')
            if s:
                extend(('        _buf.append("', q(s), '");\n', ))
        buf.append(
            '    }\n'
            )


    def expand_cont(self, buf, elem_info):
        name = elem_info.name
        extend = buf.extend
        extend((
            '    public void cont', c(name), '() {\n',
            ))
        if elem_info.cont_text_p():
            extend((
            '        if (text', c(name), ' != ', self.nullvalue, ')\n'
            '            _buf.append(text', c(name), ');\n'
            ))
        else:
            extend((
            '        if (text', c(name), ' != ', self.nullvalue, ') {\n'
            '            _buf.append(text', c(name), ');\n'
            '            return;\n'
            '        }\n',
            ))
            if elem_info.cont_stmts:
                self.expand_items(buf, elem_info.cont_stmts)
        buf.append(
            '    }\n'
            )


    def expand_etag(self, buf, elem_info):
        name = elem_info.name
        extend = buf.extend
        etag = elem_info.etag_info
        extend((
            '    public void etag', c(name), '() {\n',
            ))
        if not etag:
            extend((
            '        //\n'
            ))
        elif etag.tagname:
            s1 = q(etag.head_space or '')
            s2 = q(etag.tail_space or '')
            extend((
            '        _buf.append("', s1, '</', etag.tagname, '>', s2, '");\n',
            ))
        else:
            s = (etag.head_space or '') + (etag.tail_space or '')
            if s:
                extend(('        _buf.append("', q(s), '");\n', ))
            else:
                buf.append('        //\n')
        buf.append(
            '    }\n'
            )
