###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'

require 'kwartzite/translator/ruby'
require 'kwartzite/parser/text'


module Kwartzite


  class RubyTranslator::TestCase
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

    EXPECTED2 = <<'END'
##
## generated from foo-bar.html by rbKwartzite
##

require 'kwartzite/html'

module View
  module Html
  end
end unless defined?(View::Html)

class View::Html::FooBar_ < Kwartzite::HtmlTemplate

  def elem_DOCUMENT()
    @_buf << %Q`<div>\n`
    elem_user_form()
    @_buf << %Q`</div>\n`
  end

  ######## mark:user_form ########

  def elem_user_form(attrs=nil)
    stag_user_form(attrs)
    cont_user_form()
    etag_user_form()
  end

  def attr_user_form()
    @attr_user_form ||= {
      :action => SafeStr.new("#"),
    }
  end

  def stag_user_form(attrs=nil)
    if attrs.nil?
      @_buf << %Q`  <form action="#">\n`
    else
      @_buf << %Q`  <form`
      attr_user_form().merge(attrs).each_pair do |k, v|
        @_buf << %Q` #{k}="#{escape(v)}"` unless v.nil?
      end
      @_buf << %Q`>\n`
    end
  end

  def cont_user_form()
    @_buf << %Q`    <p>
      <label>Name</label>\n`
    elem_user_name()
    @_buf << %Q`    </p>
    <input type="submit">\n`
  end

  def etag_user_form()
    @_buf << %Q`  </form>\n`
  end

  ######## mark:user_name ########

  def elem_user_name(attrs=nil)
    stag_user_name(attrs)
    cont_user_name()
    etag_user_name()
  end

  def attr_user_name()
    @attr_user_name ||= {
      :type => SafeStr.new("text"),
      :name => SafeStr.new("user.name"),
      :value => SafeStr.new(""),
    }
  end

  def stag_user_name(attrs=nil)
    if attrs.nil?
      @_buf << %Q`      <input type="text" name="user.name" value="">\n`
    else
      @_buf << %Q`      <input`
      attr_user_name().merge(attrs).each_pair do |k, v|
        @_buf << %Q` #{k}="#{escape(v)}"` unless v.nil?
      end
      @_buf << %Q`>\n`
    end
  end

  def cont_user_name()
  end

  def etag_user_name()
  end

end


if __FILE__ == $0
  print View::Html::FooBar_.new.render
end
END

    EXPECTED1 = EXPECTED2.gsub(/View::Html::FooBar_/, 'FooBarHtml_') \
                        .gsub(/^module View.*?^end unless defined.*?\n/m, '')
    EXPECTED3 = EXPECTED1.gsub(/Kwartzite::HtmlTemplate/, 'My::Template')

    def test_translate
      parser = TextParser.new
      nodes = parser.parse(INPUT1)
      tr = RubyTranslator.new
      spec "returns source code of Ruby class." do
        opts = { :filename=>'foo-bar.html' }
        ok {tr.translate(nodes, opts)} == EXPECTED1
      end
      spec "accepts opts[:classname]." do
        opts = { :filename=>'foo-bar.html',
                 :classname=>'View::Html::%B_' }
        ok {tr.translate(nodes, opts)} == EXPECTED2
      end
      spec "accepts opts[:baseclass]." do
        opts = { :filename=>'foo-bar.html',
                 :baseclass=>'My::Template' }
        ok {tr.translate(nodes, opts)} == EXPECTED3
      end
    end

  end


end
