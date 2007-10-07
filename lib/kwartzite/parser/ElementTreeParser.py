###
### $Rev$
### $Release$
### $Copyright$
###


import re
try:
    ## cElementTree.XMLParser doesn't support 'doctype' handler
    #import xml.etree.cElementTree as ET
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET


import kwartzite.config as config
from kwartzite.util import escape_xml, h, isword, OrderedDict, define_properties
from kwartzite.parser import Parser, ParseError
from kwartzite.parser.TextParser import Directive



def walk_tree(element, before=None, after=None):
    if before: before(element)
    for child in element.getchildren():
        walk_tree(child, before, after)
    if after:  after(element)



class ElementTreeParser(Parser):


    _property_descriptions = (
        ('dattr'    , 'str'  , 'directive attribute name'),
        ('encoding' , 'str'  ,  'encoding name'),
        #('idflag'   , 'str'  , 'marking detection policy (all/lower/upper/none)'),
        ('idflag'   , '{all|upper|lower|none}'  , 'marking detection policy'),
        #('idflag'   , 'all/lower/upper/none'  , 'marking detection policy'),
    )
    define_properties(_property_descriptions)


    def __init__(self, dattr=None, encoding=None, idflag=None, **properties):
        Parser.__init__(self, **properties)
        if dattr    is not None:  self.dattr = dattr
        if encoding is not None:  self.encoding = encoding
        if idflag   is not None:  self.idflag = idflag


    def _parse_document(self, input, parser=None):
        tree = ET.ElementTree()
        parser = parser or self._create_parser(tree)
        if getattr(input, 'read', None):
            data = input.read(1024)
            while data:
                parser.feed(data)
                data = input.read(1024)
        else:
            parser.feed(input)
        elem = parser.close()
        tree._setroot(elem)
        return tree


    def _create_parser(self, tree):
        parser = ET.XMLTreeBuilder()
        def doctype_handler(name, pubid, system):
            setattr(tree, '_doctype', (name, pubid, system))
        parser.doctype = doctype_handler
        return parser


    def parse(self, input, filename=None):
        self.filename = filename
        tree = self._parse_document(input)
        elem_table = OrderedDict()
        name_table = {}
        get_directive = self.get_directive
        check_directive = self.check_directive
        def handle_directive(elem):
            directive = get_directive(elem)
            if directive:
                check_directive(directive, name_table)
                elem_table[id(elem)] = (elem, directive)
        walk_tree(tree.getroot(), handle_directive)
        return tree, elem_table, filename


    def get_directive(self, elem):
        a_name = self.dattr   # default: 'kw:d'
        a_value = elem.get(a_name)
        if a_value:
            m = re.match(r'^(\w+):(.*)', value)
            if m:
                d_name, d_arg = m.group(1), m.group(2)
                del elem.attrib[a_name]
                return Directive(d_name, d_arg, a_name, a_value)
        a_name = 'id'
        a_value = elem.get(a_name)
        if a_value:
            m = re.match(r'^(\w+):(.*)', a_value)
            if m:
                d_name, d_arg = m.group(1), m.group(2)
                del elem.attrib[a_name]
                return Directive(d_name, d_arg, a_name, a_value)
            if re.match(r'^\w+$', a_value):
                d_name, d_arg = 'mark', a_value
                idflag = self.idflag
                if idflag == 'all' or \
                   idflag == 'lower' and d_arg[0].islower() or \
                   idflag == 'upper' and d_arg[0].isupper() :
                    return Directive(d_name, d_arg, a_name, a_value)
        return None


    def check_directive(self, directive, name_table):
        if directive.name not in ('mark', 'text', 'attr', 'textattr', 'node', 'dummy'):
            raise self._error('unknown directive.', directive)
        if not re.match(r'^\w+$', directive.arg):
            raise self._error('invalid name.', directive)
        if name_table.has_key(directive.arg):
            raise self._error('marking name duplicated.', directive)


    def _error(self, message, directive):
        d = directive
        return ParseError('%s="%s": %s' % (d.attr_name, d.attr_value, message))



if __name__ == '__main__':

    import sys
    for arg in sys.argv[1:]:
        filename = arg
        parser = ElementTreeParser()
        xmldoc, elem_table, filename = parser.parse_file(filename)
        print ET.dump(xmldoc)
        print "-----------"
        for object_id, T in elem_table.iteritems():
            elem, directive = T
            print repr(elem), directive.attr_string()
