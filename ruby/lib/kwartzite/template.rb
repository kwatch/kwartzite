###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'kwartzite/safestr'


module Kwartzite


  class Template
    include SafeStr::Helper

    def [](name)
      instance_variable_get("@#{name}")
    end

    def []=(name, value)
      instance_variable_set("@#{name}", value)
    end

    def context(values={})
      values.each_pair {|k, v| instance_variable_set("@#{k}", v) }
      self
    end

    def render(context=nil)
      self.context(context) if context
      return create_document()
    end

    def render_elem(mark, context=nil)
      self.context(context) if context
      @_buf = ''
      __send__("elem_#{mark}")
      return @_buf
    end

    def create_document()
      @_buf = ''
      elem_DOCUMENT()
      return @_buf
    end

    def elem_DOCUMENT()
    end

    def echo(value)
      #@_buf << (value.is_a?(SafeStr) ? value : escape(value))
      @_buf << escape(value)
    end

    def escape(value)
      value.to_s
    end

  end


end
