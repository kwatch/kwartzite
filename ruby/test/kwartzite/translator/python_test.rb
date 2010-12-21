###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'

require 'kwartzite/translator/python'
require 'kwartzite/parser/text'


module Kwartzite


  class PythonTranslator::TestCase
    include Oktest::TestCase

    INPUT1 = <<'END'
<div>
  <form action="#" data-kwd="mark:user_form">
    <p>
      <label>Name</label>
      <input type="text" name="user.name" value="" data-kwd="mark:user_name">
    </p>
    <input type="submit">
  </form>
</div>
END

    EXPECTED1 = <<'END'
##
## generated from foo-bar.html by rbKwartzite
##

import kwartzite
from kwartzite import SafeStr


class FooBarHtml_(kwartzite.html.HtmlTemplate):

    def elem_DOCUMENT(self):
        self._buf.append('''<div>\n''')
        self.elem_user_form()
        self._buf.append('''</div>\n''')

    ######## mark:user_form ########

    def elem_user_form(self, attrs=None):
        self.stag_user_form(attrs)
        self.cont_user_form()
        self.etag_user_form()
    _elem_user_form = elem_user_form

    attr_user_form = {
        'action': SafeStr('#'),
    }

    def stag_user_form(self, attrs=None):
        if attrs is None:
            self._buf.append('''  <form action="#">\n''')
        else:
            self._buf.append('''  <form''')
            dct = self.attr_user_form.copy()
            dct.update(attrs)
            for k, v in dct.iteritems():
                if v is not None:
                    self._buf.extend((' ', k, '="', escape(v), '"'))
            self._buf.append('''>\n''')
    _stag_user_form = stag_user_form

    def cont_user_form(self):
        self._buf.append('''    <p>
      <label>Name</label>\n''')
        self.elem_user_name()
        self._buf.append('''    </p>
    <input type="submit">\n''')
    _cont_user_form = cont_user_form

    def etag_user_form(self):
        self._buf.append('''  </form>\n''')
    _etag_user_form = etag_user_form

    ######## mark:user_name ########

    def elem_user_name(self, attrs=None):
        self.stag_user_name(attrs)
        self.cont_user_name()
        self.etag_user_name()
    _elem_user_name = elem_user_name

    attr_user_name = {
        'type': SafeStr('text'),
        'name': SafeStr('user.name'),
        'value': SafeStr(''),
    }

    def stag_user_name(self, attrs=None):
        if attrs is None:
            self._buf.append('''      <input type="text" name="user.name" value="">\n''')
        else:
            self._buf.append('''      <input''')
            dct = self.attr_user_name.copy()
            dct.update(attrs)
            for k, v in dct.iteritems():
                if v is not None:
                    self._buf.extend((' ', k, '="', escape(v), '"'))
            self._buf.append('''>\n''')
    _stag_user_name = stag_user_name

    def cont_user_name(self):
    _cont_user_name = cont_user_name

    def etag_user_name(self):
        pass
    _etag_user_name = etag_user_name



if __name__ == '__main__':
    import sys
    sys.stdout.write(FooBarHtml_().render())

END

    EXPECTED2 = EXPECTED1.gsub(/FooBarHtml_/, 'FooBarView_')
    EXPECTED3 = EXPECTED1.gsub(/kwartzite\.html\.HtmlTemplate/, 'object')

    def test_translate
      parser = TextParser.new
      nodes = parser.parse(INPUT1)
      tr = PythonTranslator.new
      spec "returns source code of Python class." do
        opts = { :filename=>'foo-bar.html' }
        ok {tr.translate(nodes, opts)} == EXPECTED1
      end
      spec "accepts opts[:classname]." do
        opts = { :filename=>'foo-bar.html',
                 :classname=>'%BView_' }
        ok {tr.translate(nodes, opts)} == EXPECTED2
      end
      spec "accepts opts[:baseclass]." do
        opts = { :filename=>'foo-bar.html',
                 :baseclass=>'object' }
        ok {tr.translate(nodes, opts)} == EXPECTED3
      end
    end

  end


end
