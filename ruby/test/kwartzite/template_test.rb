###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'

require 'kwartzite/template'


module Kwartzite


  class Template::TestCase
    include Oktest::TestCase

    class DummyTemplate1 < Template
      def elem_DOCUMENT()
        instance_variables.each do |name|
          next if name =~ /^@_/
          value = instance_variable_get(name)
          @_buf << "#{name}=#{value.inspect}\n"
        end
      end
    end

    def before
      @template = Template.new
    end

    def test___getitem__  #define_method "test_[]" do
      spec "get instance variable." do
        t = @template
        t.instance_variable_set('@foo', 123)
        ok {t[:foo]} == 123
        ok {t['foo']} == 123
      end
    end

    def test___setitem__
      t = @template
      spec "set instance variable." do
        t[:foo] = 123
        ok {t.instance_variable_get('@foo')} == 123
        t['bar'] = 456
        ok {t.instance_variable_get('@bar')} == 456
      end
    end

    def test_context
      t = @template
      spec "set values as instance variables." do
        t.context(:x=>10, :y=>20)
        ok {t[:x]} == 10
        ok {t[:y]} == 20
      end
      spec "returns self." do
        ok {t.context()}.same?(t)
      end
    end

    def test_render
      spec "returns document string." do
        t = DummyTemplate1.new
        t[:x] = 123
        ok {t.render()} == "@x=123\n"
      end
      spec "can take context values." do
        t = DummyTemplate1.new
        ok {t.render(:y=>456)} == "@y=456\n"
      end
    end

    def test_echo
      t = @template
      t.init()
      spec "append value into @_buf with escaping" do
        t.echo 'abc<>&"'
        ok {t.instance_variable_get('@_buf')} == 'abc<>&"'
        def t.escape(arg)
          arg.to_s.gsub(/</, '&lt;').gsub(/>/, '&gt;')
        end
        t.echo 'abc<>&"'
        ok {t.instance_variable_get('@_buf')} == 'abc<>&"abc&lt;&gt;&"'
      end
    end

    def test_escape
      t = @template
      t.init()
      spec "convert value into escaped string." do
        ok {t.escape({:a=>1})} == {:a=>1}.to_s
      end
    end

  end


end
