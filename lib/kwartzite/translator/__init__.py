###
### $Rev$
### $Release$
### $Copyright$
###


import os, re
import kwartzite.config as config
from kwartzite.util import parse_name_pattern, build_values_from_filename



class Translator(object):


    _property_descriptions = ()   # tuple of ('name', 'default', 'description')


    def __init__(self, **properties):
        self.properties = properties


    def translate(self, template_info, **kwargs):
        """translate TemplateInfo into class definition."""
        raise NotImplementedError("%s#translate() is not implemented." % self.__class__.__name__)


    def build_classname(self, filename, pattern=None, **kwargs):
        values = self._build_values(filename)
        s = parse_name_pattern(pattern or config.CLASSNAME, values)
        #classname = re.sub('[^\w]', '_', s)
        classname = s
        return classname


    def _build_values(self, filename):
        return build_values_from_filename(filename)
