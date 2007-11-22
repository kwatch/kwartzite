###
### $Rev$
### $Release$
### $Copyright$
###

class BaseConfig(object):
    ESCAPE    = False
    ENCODING  = None    # or 'utf-8'
    CLASSNAME = '%u_%x'

class ParserConfig(BaseConfig):
    NO_ETAGS  = [ 'input', 'img' ,'br', 'hr', 'meta', 'link' ]   # end-tag is omittable
    DELSPAN   = True    # delete dummy <span> tag
    DATTR     = 'kw:d'
    IDFLAG    = 'all'   # or 'upper', 'lower', 'none'

class TextParserConfig(ParserConfig):
    pass

class XmlParserConfig(ParserConfig):
    pass

class ElementTreeParserConfig(ParserConfig):
    pass

class TranslatorConfig(BaseConfig):
    BASECLASS = 'object'
    MAINPROG  = True
    CONTEXT   = None
    NULLOBJ   = False
    FRAGMENT  = False
    ATTROBJ   = True
    ACCESSORS = True

class PythonTranslatorConfig(TranslatorConfig):
    CLASSNAME = '%u_%x'
    BASECLASS = 'object'
    CONTEXT   = True

class JavaTranslatorConfig(TranslatorConfig):
    CLASSNAME = '%U%X'
    BASECLASS = 'Object'
    INTERFACE = None
    PACKAGE   = None
    CONTEXT   = False
    JAVA5     = True

class ElementTreeTranslatorConfig(TranslatorConfig):
    pass
