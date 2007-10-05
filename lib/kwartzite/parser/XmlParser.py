###
### $Rev$
### $Release$
### $Copyright$
###


import sys, re
from xml.parsers.expat import ParserCreate
import kwartzite.config as config
from kwartzite.util import escape_xml, h, isword, OrderedDict, define_properties
from kwartzite.parser.TextParser import TagInfo, BaseParser



class XmlParser(BaseParser):


    def parse_file(self, filename):
        #input = open(filename)
        input = open(filename).read()
        self.parse(self, input, filename)


    def _setup(self, input, filename):
        BaseParser._setup(self, input, filename)
        items = []
        if isinstance(input, file):
            input = input.read()
        xmlparser = self._create_xmlparser(items, input)
        #if isinstance(input, file):
        #    xmlparser.ParseFile(input)
        #    input = None
        #else:
        #    xmlparser.Parse(input, True)
        xmlparser.Parse(input, True)     ## parse xml document
        self._end_document_handler()
        tuples = self._pack(items)
        def create_generator(tuples):
            for t in tuples:
                yield t
        gen = create_generator(tuples)
        self._fetch = gen.next


    def _create_xmlparser(self, items, input):
        xmlparser = ParserCreate()
        xmlparser.buffer_text = True
        xmlparser.ordered_attributes = True
        pos = [0]
        is_xmldecl = [None]
        import sys; w = sys.stderr.write
        items.append('')   # dummy string
        #
        if not self.encoding:
            self.encoding = 'utf-8'
        def e(s):
            if isinstance(s, unicode):
                return s.encode(self.encoding)
            return s
        #
        def set_tag_string():
            index = xmlparser.CurrentByteIndex
            s = input[pos[0]:index]
            if isinstance(items[-1], TagInfo):
                items[-1].string = s
            else:
                #items.append(s)
                assert items[-1] == ''  # dummy string
                items[-1] = s
            pos[0] = index
        #
        def start_element_handler(tagname, attrs):
            set_tag_string()
            L = attrs
            attrs = [ (e(h(L[i])), e(h(L[i+1]))) for i in xrange(0, len(L), 2) ]
            tag = TagInfo(e(tagname), attrs, False)
            tag.linenum = xmlparser.CurrentLineNumber
            items.append(tag)
        xmlparser.StartElementHandler = start_element_handler
        #
        def end_element_handler(tagname):
            index = xmlparser.CurrentByteIndex
            if input[index-2:index] == '/>':
                assert isinstance(items[-1], TagInfo)
                if items[-1].name == tagname:
                    tag = items[-1]
                    tag.is_empty = True
                    tag.is_etag = False
                    return
            set_tag_string()
            tag = TagInfo(e(tagname), None, True)
            tag.linenum = xmlparser.CurrentLineNumber
            items.append(tag)
        xmlparser.EndElementHandler = end_element_handler
        #
        def default_handler(string):
            if items and isinstance(items[-1], TagInfo):
                index = xmlparser.CurrentByteIndex
                s = input[pos[0]:index]
                items[-1].string = s
                pos[0] = index
                items.append('')   # dummy string
            #items.append(e(string))   # unicode
        xmlparser.DefaultHandler = default_handler
        #
        #def xml_decl_handler(version, encoding, standalone):
        #    self.encoding = encoding
        #
        def end_document_handler():
            set_tag_string()
        #xmlparser.EndDocumentHandler = default_handler
        self._end_document_handler = end_document_handler
        #
        return xmlparser


    def _pack(self, items):
        L = []  # tuples
        pos = 0
        i = -1
        for item in items:
            i += 1
            if isinstance(item, TagInfo):
                tag = item
                #text = i > pos and ''.join(items[pos:i]) or ''
                if   i == pos:      text = ''
                elif i == pos + 1:  text = items[pos]
                else:               text = ''.join(items[pos:i])
                #assert 0 <= i - pos <= 1
                #text = i > pos and items[pos] or ''
                L.append((text, tag))
                pos = i + 1
            else:
                #assert isinstance(item, unicode) or isinstance(item, str)
                pass
        text = i >= pos and ''.join(items[pos:i+1]) or ''
        tag = None
        L.append((text, tag))
        return L  # tuples
