###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'kwartzite/template'
require 'kwartzite/safestr'
require 'kwartzite/util'


module Kwartzite


  module Html

    module_function

    def escape(value)
      value.is_a?(SafeStr) ? value : escape_html(value)
    end

    ESCAPE_HTML = { '&'=>'&amp;', '<'=>'&lt;', '>'=>'&gt;', '"'=>'&quot;', "'"=>'&039;' }

    def escape_html(value)
      SafeStr.new(value.to_s.gsub(/[&<>"]/) { ESCAPE_HTML[$&] })
    end

    def escape_html2(value)
      SafeStr.new(value.to_s.gsub(/&/, '&amp;').gsub(/</, '&lt;').gsub(/>/, '&gt;').gsub(/"/, '&quot;'))
    end

    def new_cycle(*values)
      values = values.collect {|v| escape(v) }
      return Util::Cycle.new(*values)
    end

  end


  class HtmlTemplate < Template
    include Html
  end


end
