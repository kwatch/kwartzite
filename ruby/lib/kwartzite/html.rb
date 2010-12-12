###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'kwartzite/template'
require 'kwartzite/safe_str'
require 'kwartzite/util'


module Kwartzite


  module Html

    module_function

    def escape(value)
      #: escapes html special characters unless value is a SafeStr.
      value.is_a?(SafeStr) ? value : escape_html(value)
    end

    ESCAPE_HTML = { '&'=>'&amp;', '<'=>'&lt;', '>'=>'&gt;', '"'=>'&quot;', "'"=>'&039;' }

    def escape_html(value)
      #: escapes html special characters.
      #: returns SafeStr object.
      SafeStr.new(value.to_s.gsub(/[&<>"]/) { ESCAPE_HTML[$&] })
    end

    def escape_html2(value)
      #: escapes html special characters.
      #: returns SafeStr object.
      SafeStr.new(value.to_s.gsub(/&/, '&amp;').gsub(/</, '&lt;').gsub(/>/, '&gt;').gsub(/"/, '&quot;'))
    end

    def new_cycle(*values)
      #: escapes all values.
      values = values.collect {|v| escape(v) }
      #: returns new Cycle object.
      return Util::Cycle.new(*values)
    end

    CHECKED  = SafeStr.new('checked').freeze
    SELECTED = SafeStr.new('selected').freeze
    DISABLED = SafeStr.new('disabled').freeze

    def checked(value)
      #: returns 'checked' if true value.
      #: returns nil if false value.
      value ? CHECKED : nil
    end

    def selected(value)
      #: returns 'selected' if true value.
      #: returns nil if false value.
      value ? SELECTED : nil
    end

    def disabled(value)
      #: returns 'disabled' if true value.
      #: returns nil if false value.
      value ? DISABLED : nil
    end

  end


  class HtmlTemplate < Template
    include Html
  end


end
