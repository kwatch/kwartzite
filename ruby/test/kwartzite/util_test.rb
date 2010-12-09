###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'oktest'

require 'kwartzite/util'


module Kwartzite


  class Util::Cycle::TestCase
    include Oktest::TestCase

    def test_value
      spec "returns next value cyclicly." do
        c = Util::Cycle.new('A', 'B', 'C')
        ok {c.value} == 'A'
        ok {c.value} == 'B'
        ok {c.value} == 'C'
        ok {c.value} == 'A'
        ok {c.value} == 'B'
        ok {c.value} == 'C'
        ok {c.value} == 'A'
      end
    end

    def test_to_s
      spec "returns next value cyclicly." do
        c = Util::Cycle.new('A', 'B', 'C')
        ok {"#{c}"} == 'A'
        ok {"#{c}"} == 'B'
        ok {"#{c}"} == 'C'
        ok {"#{c}"} == 'A'
        ok {"#{c}"} == 'B'
        ok {"#{c}"} == 'C'
        ok {"#{c}"} == 'A'
      end
    end

  end


  class Util::TestCase
    include Oktest::TestCase
    include Kwartzite::Util

    def _test(fmt, filepath='some/where/foo-bar.html')
      Kwartzite::Util::name_format(fmt, filepath)
    end

    def test_name_format
      spec "'%%' -> '%'." do
        ok {_test('%%')} == '%'
      end
      spec "'%f' -> 'foo-bar.html'." do
        ok {_test('%f')} == 'foo-bar.html'
      end
      spec "'%x' -> 'html'." do
        ok {_test('%x')} == 'html'
      end
      spec "'%b' -> 'foo-bar'." do
        ok {_test('%b')} == 'foo-bar'
      end
      spec "'%u' -> 'foo_bar'." do
        ok {_test('%u')} == 'foo_bar'
      end
      spec "'%d' -> 'some/where'." do
        ok {_test('%d')} == 'some/where'
      end
      spec "'%c' -> 'foo_bar_html'." do
        ok {_test('%c')} == 'foo_bar_html'
      end
      spec "'%F' -> 'FooBarHtml'." do
        ok {_test('%F')} == 'FooBarHtml'
      end
      spec "'%X' -> 'Html'." do
        ok {_test('%X')} == 'Html'
      end
      spec "'%B' -> 'FooBar'." do
        ok {_test('%B')} == 'FooBar'
      end
      spec "'%U' -> 'FooBar'." do
        ok {_test('%U')} == 'FooBar'
      end
      spec "'%D' -> 'SomeWhere'." do
        ok {_test('%D')} == 'SomeWhere'
      end
      spec "'%C' -> 'FooBarHtml'." do
        ok {_test('%C')} == 'FooBarHtml'
      end
      spec "raises error when unknown format character." do
        pr = proc { _test('%1') }
        ok {pr}.raise?(ArgumentError, "%1: unknown format for class name.")
      end
    end

    def test__camelcase
      spec "'foo-bar.html' -> 'FooBarHtml'" do
        ok {Util.__send__(:_camelcase, 'foo-bar.html')} == 'FooBarHtml'
      end
    end

  end


end
