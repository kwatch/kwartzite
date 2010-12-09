###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'

require 'kwartzite'


class DummyParser1 < Kwartzite::Parser

  def parse(*args)
    return "args=#{args.inspect}"
  end

end


module Kwartzite


  class Parser::TestCase
    include Oktest::TestCase

    def test_initialize
      spec "set @directive_attr." do
        ok {Parser.new(:d_attr=>'id').d_attr} == 'id'
      end
      spec "if :d_attr is not passed then use DIRECTIVE_ATTR instead." do
        ok {Parser.new().d_attr} == Kwartzite::DIRECTIVE_ATTR
      end
    end

    def test_parse_file
      spec "read file and pass it to parse()." do
        parser = DummyParser1.new
        expected = [File.open(__FILE__, 'rb') {|f| f.read }, __FILE__]
        ok {parser.parse_file(__FILE__)} == "args=#{expected.inspect}"
      end
    end

    def test_SELF_register
      spec "regsiter klass with lang." do
        Parser.register('dummy1', DummyParser1)
        ok {Parser.instance_variable_get('@registered')['dummy1']} == DummyParser1
      end
    end

    def test_SELF_get_class
      spec "return klass object registered with lang." do
        Parser.register('dummy1b', DummyParser1)
        ok {Parser.get_class('dummy1b')} == DummyParser1
      end
    end

  end


  class Tag::TestCase
    include Oktest::TestCase

    def before
      @stag = Tag.new(:stag, 'div', {})
      @etag = Tag.new(:etag, 'div', {})
      @empty = Tag.new(:empty, 'div', {})
    end

    def test_stag?
      spec "return true if start-tag." do
        ok {@stag.stag?} == true
        ok {@etag.stag?} == false
        ok {@empty.stag?} == false
      end
    end

    def test_etag?
      spec "return true if end-tag." do
        ok {@stag.etag?} == false
        ok {@etag.etag?} == true
        ok {@empty.etag?} == false
      end
    end

    def test_empty?
      spec "return true if empty-tag." do
        ok {@stag.empty?} == false
        ok {@etag.empty?} == false
        ok {@empty.empty?} == true
      end
    end

    def test_set_directive
      spec "return self." do
        ok {@stag.set_directive('mark:foo')}.same?(@stag)
      end
      spec "set directive value." do
        #falldown
        ok {@stag.directive} == 'mark:foo'
      end
    end

    def test_has_directive?
      spec "return true if directive is set." do
        ok {@stag.has_directive?} == false
        @stag.set_directive('mark:foo')
        ok {@stag.has_directive?} == true
      end
    end

    def test_set_spaces
      spec "return self." do
        ok {@stag.set_spaces('  ', '   ', '    ')}.same?(@stag)
      end
      spec "set left-space, tail-space, and right-space." do
        #falldown
        ok {@stag.l_space}    == '  '
        ok {@stag.tail_space} == '   '
        ok {@stag.r_space}    == '    '
      end
    end

    def test_to_s
      spec "return html tag string." do
        @stag.attrs = [["  ", "id", "123"], ["  ", "class", "main"]]
        @stag.set_spaces('  ', "\t\n", "   \n")
        ok {@stag.to_s} == %Q`  <div  id="123"  class="main"\t\n>   \n`
      end
    end

  end


  class Element::TestCase
    include Oktest::TestCase

    def test_normalize
      spec "concat sequencial strings in nodes into a string." do
        e1 = Element.new(nil, nil, [])
        e2 = Element.new(nil, nil, [])
        nodes = ["AAA", "BBB", e1, e2, "CCC", "DDD"]
        elem = Element.new(nil, nil, [])
        ok {elem.__send__(:normalize, nodes)} == ["AAABBB", e1, e2, "CCCDDD"]
      end
    end

    def test_initialize
      spec "normalize child nodes." do
        e1 = Element.new(nil, nil, [])
        e2 = Element.new(nil, nil, [])
        children = ["AAA", "BBB", e1, e2, "CCC", "DDD"]
        elem = Element.new(nil, nil, children)
        ok {elem.children} == ["AAABBB", e1, e2, "CCCDDD"]
      end

    end

  end


end
