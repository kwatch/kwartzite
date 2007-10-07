###
### $Rev$
### $Release$
### $Copyright$
###


import re
try:
    #import xml.etree.cElementTree as ET
    import xml.etree.ElementTree as ET
except:
    #import elementtree.cElementTree as ET
    import elementtree.ElementTree as ET


import kwartzite.config as config
from kwartzite.util import escape_xml, h, isword, OrderedDict, define_properties
from kwartzite.translator import Translator



def q(string):
    s = quote(string)
    if s.endswith("\r\n"):
        return s[0:-2] + "\\r\\n"
    if s.endswith("\n"):
        return s[0:-1] + "\\n"
    return s



def walk_thru(elem, func):
    for child in elem.getchildren():
        ret = func(child, elem)
        if ret is not False:
            walk_thru(child, func)



class ElementTreeTranslator(Translator):


    _property_descriptions = (
        ('classname' , 'str' , 'classname pattern'),
        ('baseclass' , 'str' , 'parent class name'),
        ('encoding'  , 'str' , 'encoding name'),
        ('mainprog'  , 'bool', 'define main program or not'),
        ('context'   , 'bool', 'use context object in constructor or not'),
    )
    define_properties(_property_descriptions, baseclass='object')
    if locals()['baseclass'] is 'Object':  locals()['baseclass'] = 'object'


    def __init__(self, classname=None, baseclass=None, encoding=None, mainprog=None, context=None, **properties):
        Translator.__init__(self, **properties)
        if classname   is not None:  self.classname = classname
        if baseclass   is not None:  self.baseclass = baseclass
        if encoding    is not None:  self.encoding  = encoding
        if mainprog    is not None:  self.mainprog  = mainprog
        if context     is not None:  self.context   = context
        ##
        self.num = 0
        self.num_table = {}


    def translate(self, template_info, **properties):
        xmldoc, elem_table, filename = template_info
        if properties.has_key('filename'): filename = properties['filename']
        classname  = properties.get('classname') or self.classname
        classname = self.build_classname(filename, pattern=classname, **properties)
        buf = []
        extend = buf.extend
        append = buf.append
        #
        if self.encoding:
            append('# -*- coding: %s -*-\n' % self.encoding)
        if filename:
            append('## generated from %s\n' % filename)
        append('\n')
        append('try:\n'
               '    import xml.etree.cElementTree as ET\n'
               'except ImportError:\n'
               '    try:\n'
               '        import elementtree.cElementTree as ET\n'
               '    except ImportError:\n'
               '        import elementtree.ElementTree as ET\n'
               'Element = ET.Element\n'
               'SubElement = ET.SubElement\n'
               '\n'
               '\n')
        #
        append("__all__ = ['%s']\n" % classname)
        append("\n")
        #
        append("\n"
               "class %s(%s):\n"
               "\n" % (classname, self.baseclass))
        flag = False
        if self.context:
            append('    def __init__(self, **_context):\n'
                   '        for k, v in _context.iteritems():\n'
                   '            setattr(self, k, v)\n'
                   '        self._context = _context\n')
            flag = True
        #
        for object_id, T in elem_table.iteritems():
            elem, directive = T
            d_name, d_arg = directive.name, directive.arg
            if d_name in ('mark', 'attr', 'textattr'):
                if not flag:
                    append("    def __init__(sefl):\n")
                    flag = True
                append("        self.attr_%s = self.attr_%s.copy()\n" % (d_arg, d_arg))
        if flag:
            append("\n")
        #
        append(    '    def create_document(self):\n')
        elem = xmldoc.getroot()
        T = elem_table.get(id(elem))
        n = self.next_number()
        if T:
            assert elem is T[0]
            func = self._gencode(buf, elem_table, parent_varname=None)
            func(elem, None)
        else:
            append("        root = e%d = Element(%s, %s)\n" % (n, repr(elem.tag), repr(elem.attrib)))
            append("        e%d.text = %s\n" % (n, repr(elem.text)))
            append("        e%d.tail = %s\n" % (n, repr(elem.tail)))
            self.expand_children(buf, elem, elem_table, parent_varname="e%d"%n)
        append(    "        return ET.ElementTree(root)\n")
        append(    "\n")
        #
        for object_id, T in elem_table.iteritems():
            elem, directive = T
            d_arg = directive.arg
            append("\n"
                   "    ## element '%s'\n"
                   "\n" % d_arg)
            self.expand_elem(buf, elem, elem_table, directive)
        #
        if self.mainprog:
            append("\n"
                   "# for test\n"
                   "if __name__ == '__main__':\n"
                   "    ET.dump(%s().create_document()),\n"
                   "\n" % classname)
        return ''.join(buf)


    def next_number(self):
        n = self.num
        self.num = n = n + 1
        return n


    def expand_children(self, buf, elem, elem_table, parent_varname='parent'):
        func = self._gencode(buf, elem_table, parent_varname)
        walk_thru(elem, func)


    def _gencode(self, buf, elem_table, parent_varname):
        append = buf.append
        elem_nums = {}
        def gencode(elem, parent):
            assert parent is not None or parent_varname is None
            code = None
            text_expr = None
            attr_expr = None
            n = self.next_number()
            elem_nums[id(elem)] = n
            T = elem_table.get(id(elem))
            if T:
                assert elem is T[0]
                directive = T[1]
                d_name, d_arg = directive.name, directive.arg
                if d_name == 'mark':
                    parent_n = elem_nums.get(id(parent))
                    varname = parent and parent_n and 'e%d' % parent_n or parent_varname
                    s = not parent and 'root = ' or ''
                    append("        %sself.elem_%s(%s)\n" % (s, d_arg, varname))
                    return False
                elif d_name == 'dummy':
                    parent_n = elem_nums.get(id(parent))
                    varname = parent and parent_n and 'e%d' % parent_n or parent_varname
                    s = not parent and 'root = None ' or ''
                    append("        %s#self.elem_%s(%s)\n" % (s, d_arg, varname))
                    return False
                elif d_name == 'node':
                    raise self._error("%s doesn't support 'node' directive." %
                                      self.__class__.__name__, directive)
                else:
                    if d_name == 'attr' or d_name == 'textattr':
                        attr_expr = 'self.attr_' + d_arg
                    if d_name == 'text' or d_name == 'textattr':
                        text_expr = 'self.text_' + d_arg
            #n = self.next_number()
            #elem_nums[id(elem)] = n
            if not text_expr:  text_expr = repr(elem.text)
            if not attr_expr:  attr_expr = repr(elem.attrib)
            if parent:
                parent_n = elem_nums.get(id(parent))
                varname = parent_n is not None and 'e%d' % parent_n or parent_varname
                append("        e%d = SubElement(%s, %s, %s)\n" %
                                (n, varname, repr(elem.tag), attr_expr))
            else:
                assert parent_varname is None
                varname = 'root'
                append("        e%d = %s = Element(%s, %s)\n" %
                                (n, varname, repr(elem.tag), atr_expr))
            append(    "        e%d.text = %s\n" % (n, text_expr))
            append(    "        e%d.tail = %s\n" % (n, repr(elem.tail)))
        #
        return gencode


    def expand_elem(self, buf, elem, elem_table, directive):
        d_name, d_arg = directive.name, directive.arg
        append = buf.append
        if d_name == 'text':
            append("    text_%s = %s\n" % (d_arg, repr(elem.text)))
            append("\n")
        elif d_name == 'attr':
            append("    attr_%s = %s\n" % (d_arg, repr(elem.attrib)))
            append("\n")
        elif d_name == 'textattr':
            append("    text_%s = %s\n" % (d_arg, repr(elem.text)))
            append("    attr_%s = %s\n" % (d_arg, repr(elem.attrib)))
            append("\n")
        elif d_name == 'mark':
            append("    text_%s = %s\n" % (d_arg, repr(elem.text)))
            append("    attr_%s = %s\n" % (d_arg, repr(elem.attrib)))
            append("\n")
            n = self.next_number()
            buf.extend((
            '    def elem_%s(self, parent):\n' % d_arg,
            '        e%d = SubElement(parent, %s, self.attr_%s.copy())\n' %
                                                  (n, repr(elem.tag), d_arg),
            '        e%d.text = self.text_%s\n' % (n, d_arg),
            '        e%d.tail = %s\n' % (n, repr(elem.tail)),
            '        self.cont_%s(e%d)\n' % (d_arg, n),
            '        return e%d\n' % (n),
            '\n',
            '    def cont_%s(self, element):\n' % d_arg,
            ))
            count = len(buf)
            self.expand_children(buf, elem, elem_table, parent_varname='element')
            if count == len(buf):
                append("        pass\n")
            append("\n")
            append("    _elem_%s = elem_%s\n" % (d_arg, d_arg))
            append("    _cont_%s = cont_%s\n" % (d_arg, d_arg))
            append("\n")
        elif d_name == 'dummy':
            pass
        else:
            assert False, '** unreachable'


if __name__ == '__main__':

    import sys
    from kwartzite.parser.ElementTreeParser import ElementTreeParser
    for arg in sys.argv[1:]:
        filename = arg
        parser = ElementTreeParser()
        template_info = parser.parse_file(filename)
        xmldoc, elem_table, filename = template_info
        #print ET.dump(xmldoc)
        #print "-----------"
        for object_id, T in elem_table.iteritems():
            elem, directive = T
            #print repr(elem), directive.attr_string()
        #print "-----------"
        translator = ElementTreeTranslator()
        print translator.translate(template_info),
