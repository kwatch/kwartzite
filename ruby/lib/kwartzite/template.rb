###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'kwartzite/safestr'


module Kwartzite


  class Template

    def [](name)
      #: get instance variable.
      instance_variable_get("@#{name}")
    end

    def []=(name, value)
      #: set instance variable.
      instance_variable_set("@#{name}", value)
    end

    def init
      @_buf = ""
    end

    def context(values={})
      #: set values as instance variables.
      values.each_pair {|k, v| instance_variable_set("@#{k}", v) }
      #: returns self.
      self
    end

    def render(context=nil)
      #: can take context values.
      self.context(context) if context
      #: returns document string.
      return create_document()
    end

    def render_elem(mark, context=nil)
      self.context(context) if context
      init()
      __send__("elem_#{mark}")
      return @_buf
    end

    def create_document()
      init()
      elem_DOCUMENT()
      return @_buf
    end

    def elem_DOCUMENT()
    end

    def echo(value)
      #: append value into @_buf with escaping
      #@_buf << (value.is_a?(SafeStr) ? value : escape(value))
      @_buf << escape(value)
    end

    def escape(value)
      #: convert value into escaped string.
      value.to_s
    end

  end


end
