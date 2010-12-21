###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module Kwartzite


  class Translator

    DEFAULTS = {
      :classname => '%C_',
      :baseclass => nil,
      :escapefunc => 'escape',
    }

    def initialize(opts={})
      #: accepts opts[:escapefunc] (default is 'escape').
      @opts = self.class.const_get(:DEFAULTS).dup.merge(opts)
      @escapefunc = @opts[:escapefunc]
    end

    def translate(nodes, opts={})
      return @buf
    end

    @registered = {}

    def self.register(lang, klass)
      #: saves klass with lang as key.
      @registered[lang] = klass
    end

    def self.get_class(lang)
      #: returns object associated with lang.
      return @registered[lang]
    end

  end


end
