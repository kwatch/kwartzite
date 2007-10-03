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


    def translate(self, template_info, filename=None, classname=None, baseclass=None, encoding=None, mainprog=None, **kwargs):
        if filename is None:
            filename = template_info.filename
        if classname is None:
            classname = self.build_classname(filename, **kwargs)
        if baseclass is None:
            baseclass = self.properties.get('baseclass', 'Object')
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
        if filename:
            buf.extend(('// generated from ', filename, '\n', ))
        buf.extend((
            '\n'
            'import java.util.*;\n',
            '\n',
            '\n'
            'public class ', classname, ' extends ', baseclass, ' {\n'
            '\n'
            '    protected StringBuffer _buf = new StringBuffer();\n'
            '\n'
            '    public ', classname, '() {\n'
            ))
        for name, elem_info in elem_info_table.iteritems():
            buf.extend(('        init', c(name), '();\n', ))
        buf.extend((
            '    }\n'
            '\n',
            ))
        self.expand_utils(buf)
        buf.extend((
            '\n'
            '    public String createDocument() {\n',
            ))
        self.expand_items(buf, stmt_list)
        buf.extend((
            '        return _buf.toString();\n'
            '    }\n'
            '\n',
            ))
        for name, elem_info in elem_info_table.iteritems():
            buf.extend((
            '\n'
            '    // element \'', name, '\'\n'
            '\n'
            ))
            self.expand_init(buf, elem_info); buf.append("\n")
            self.expand_elem(buf, elem_info); buf.append("\n")
            self.expand_stag(buf, elem_info); buf.append("\n")
            self.expand_cont(buf, elem_info); buf.append("\n")
            self.expand_etag(buf, elem_info); buf.append("\n")
        if mainprog:
            buf.extend((
            '\n'
            '    // for test\n'
            '    public static void main(String[] args) {\n'
            #'        ', classname, ' template_ = new ', classname, '();\n'
            #'        String output_ = template_.createDocument();\n'
            #'        System.out.print(output_);\n'
            '        System.out.print(new ', classname, '().createDocument());\n'
            '    }\n'
            ))
        buf.append(
            '\n'
            '}\n'
            )
        return ''.join(buf)


    def expand_utils(self, buf):
        buf.append(
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
            '            if (val != null) {\n'
            #'                _buf.append(\' \').append(key).append("=\\"").append(toStr(val)).append(\'"\');\n'
            '                _buf.append(\' \').append(key).append("=\\"").append(val).append(\'"\');\n'
            '            }\n'
            '        }\n'
            '    }\n'
            )


    def expand_items(self, buf, stmt_list):
        for item in stmt_list:
            if isinstance(item, (str, unicode)):
                buf.extend(('        _buf.append("', q(item), '");\n', ))
            elif isinstance(item, ElementInfo):
                elem_info = item
                buf.extend(('        elem', c(elem_info.name), '();\n', ))
            elif isinstance(item, Expression):
                expr = item
                buf.extend(('        _buf.append(toStr(', expr.code, '));\n'))
            else:
                assert '** unreachabel'


    def expand_init(self, buf, elem_info):
        name = elem_info.name
        initval = not elem_info.cont_text_p() and ' = null' or ''
        buf.extend((
            #'    public Map attr', c(name), ' = new HashMap();\n'
            '    public Map attr', c(name), ';\n'
            '    public String text', c(name), initval, ';\n'
            '    public String node', c(name), ' = null;\n'
            '\n'
            '    public void init', c(name), '() {\n'
            ))
        ## attr_xxx
        buf.extend((
            '        attr', c(name), ' = new HashMap();\n'
            ))
        for space, aname, avalue in elem_info.attr_info:
            if isinstance(avalue, Expression):
                s = avalue.code;
            else:
                s = '"' + q(avalue) + '"'
            buf.extend((
            '        attr', c(name), '.put("', aname, '", ', s, ');\n',
            ))
        ## text_xxx
        if elem_info.cont_text_p():
            assert len(elem_info.cont_stmts) == 1
            buf.extend((
            '        text', c(name), ' = "', q(elem_info.cont_stmts[0]), '";\n'
            ))
        buf.extend((
            '    }\n',
            ))


    def expand_elem(self, buf, elem_info):
        name = elem_info.name
        buf.extend((
            '    public void elem', c(name), '() {\n'
            '        if (node', c(name), ' == null) {\n'
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
        stag = elem_info.stag_info
        buf.extend((
            '    public void stag', c(name), '() {\n'
            ))
        if stag.tagname:
            buf.extend((
            '        _buf.append("', stag.head_space or '', '<', stag.tagname, '");\n'
            '        appendAttribute(attr', c(name), ');\n'
            '        _buf.append("', q(stag.extra_space or ''), stag.is_empty and ' />' or '>', q(stag.tail_space or ''), '");\n',
            ))
        else:
            s = (stag.head_space or '') + (stag.tail_space or '')
            if s:
                buf.extend(('        _buf.append("', q(s), '");\n', ))
        buf.append(
            '    }\n'
            )


    def expand_cont(self, buf, elem_info):
        name = elem_info.name
        buf.extend((
            '    public void cont', c(name), '() {\n',
            ))
        if elem_info.cont_text_p():
            buf.extend((
            '        if (text', c(name), ' != null)\n'
            '            _buf.append(text', c(name), ');\n'
            ))
        else:
            buf.extend((
            '        if (text', c(name), ' != null) {\n'
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
        etag = elem_info.etag_info
        buf.extend((
            '    public void etag', c(name), '() {\n',
            ))
        if not etag:
            buf.extend((
            '        //\n'
            ))
        elif etag.tagname:
            s1 = q(etag.head_space or '')
            s2 = q(etag.tail_space or '')
            buf.extend((
            '        _buf.append("', s1, '</', etag.tagname, '>', s2, '");\n',
            ))
        else:
            s = (etag.head_space or '') + (etag.tail_space or '')
            if s:
                buf.extend(('        _buf.append("', q(s), '");\n', ))
            else:
                buf.append('        //\n')
        buf.append(
            '    }\n'
            )
