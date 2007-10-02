###
### $Rev$
### $Release$
### $Copyright$
###



class Translator(object):


    def __init__(self, encoding=None, **properties):
        self.encoding = encoding
        self.properties = properties


    def translate(self, template_info, **kwargs):
        """translate TemplateInfo into class definition."""
        raise NotImplementedError("%s#translate() is not implemented." % self.__class__.__name__)
