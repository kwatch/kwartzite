###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'

require 'kwartzite/translator'


module Kwartzite


  class DummyTranslator1 < Translator
  end
  class DummyTranslator2 < Translator
  end


  class Translator::TestCase
    include Oktest::TestCase

    def test_initialize
      spec "accepts opts[:escapefunc] (default is 'escape')." do
        tr = Translator.new(:escapefunc=>'h')
        ok {tr.instance_variable_get('@escapefunc')} == 'h'
        tr = Translator.new()
        ok {tr.instance_variable_get('@escapefunc')} == 'escape'
      end
    end

    def test_SELF_register
      spec "saves klass with lang as key." do
        Translator.register('dummy1', DummyTranslator1)
        ok {Translator.instance_variable_get('@registered')['dummy1']} == DummyTranslator1
      end
    end

    def test_SELF_get_class
      Translator.register('dummy2', DummyTranslator2)
      spec "returns object associated with lang." do
        ok {Translator.get_class('dummy2')} == DummyTranslator2
      end
    end

  end


end
