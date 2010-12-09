###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'

#require 'kwartzite/director'
#require 'kwartzite/parser/text'
#require 'kwartzite/translator/ruby'
require 'kwartzite'


module Kwartzite


  class Director::TestCase
    include Oktest::TestCase

    def test_initialize
      spec "merges opts with DEFAULTS." do
        director = Director.new
        ok {director.opts} == Director::DEFAULTS
        director = Director.new(:classname=>'View::%C_', :escapefunc=>'h')
        ok {director.opts[:classname]} == 'View::%C_'
        ok {director.opts[:escapefunc]} == 'h'
        ok {director.opts} == Director::DEFAULTS.merge({:classname=>'View::%C_', :escapefunc=>'h'})
      end
      spec "get parser." do
        ok {Director.new.instance_variable_get('@parser')}.is_a?(TextParser)
      end
      spec "get translator." do
        ok {Director.new.instance_variable_get('@translator')}.is_a?(RubyTranslator)
      end
    end

    def test_construct
      director = Director.new
      filename = "foo-bar-baz.html"
      spec "parse html file and translate it into class definition." do
        dummy_file filename=>INPUT1 do
          ok {director.construct(filename)} == EXPECTED1
        end
      end
    end

    INPUT1 = <<'END'
<html>
  <body>
    <form action="#" data-kwd="mark:user_form">
      <p>
       <label>Name</label>
       <input type="text" name="user.name" value="" data-kwd="mark:user_name">
      </p>
    </form>
  </body>
</html>
END

    EXPECTED1 = <<'END'
##
## generated from foo-bar-baz.html by rbKwartzite
##

require 'kwartzite/html'


class FooBarBazHtml_ < Kwartzite::HtmlTemplate

  def elem_DOCUMENT()
    @_buf << %Q`<html>
  <body>\n`
    elem_user_form()
    @_buf << %Q`  </body>
</html>\n`
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
      @_buf << %Q`    <form action="#">\n`
    else
      @_buf << %Q`    <form`
      attr_user_form().merge(attrs).each_pair do |k, v|
        @_buf << %Q` #{k}="#{escape(v)}"` unless v.nil?
      end
      @_buf << %Q`>\n`
    end
  end

  def cont_user_form()
    @_buf << %Q`      <p>
       <label>Name</label>\n`
    elem_user_name()
    @_buf << %Q`      </p>\n`
  end

  def etag_user_form()
    @_buf << %Q`    </form>\n`
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
      @_buf << %Q`       <input type="text" name="user.name" value="">\n`
    else
      @_buf << %Q`       <input`
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
  print FooBarBazHtml_.new.render
end
END

  end


end
