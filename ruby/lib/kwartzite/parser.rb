###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module Kwartzite


  DIRECTIVE_ATTR = 'data-kwd'


  class Parser

    def initialize(opts={})
      @directive_attr = opts[:d_attr] || DIRECTIVE_ATTR
    end

    attr_accessor :d_attr

    def parse_file(filename)
      return parse(File.open(filename, 'rb').read, filename)
    end

    def parse(input, filename='(unknown)')
      # abstract
    end

    @registered = {}

    def self.register(lang, klass)
      @registered[lang] = klass
    end

    def self.get_class(lang)
      return @registered[lang]
    end

  end


  class Tag

    def initialize(kind, name, attrs, string=nil)
      @kind, @name, @attrs, @string = kind, name, attrs, string
      @end_slash   = @kind == :etag ? '/' : nil
      @empty_slash = @kind == :empty ? '/' : nil
    end

    attr_accessor :kind, :name, :attrs, :string
    attr_accessor :empty_slash

    def stag?
      @kind == :stag
    end

    def etag?
      @kind == :etag
    end

    def empty?
      @kind == :empty
    end

    def set_directive(directive)
      @directive = directive
      return self
    end

    def has_directive?
      !! @directive
    end

    attr_accessor :directive

    def set_spaces(l_space, tail_space, r_space)
      @l_space, @tail_space, @r_space = l_space, tail_space, r_space
      return self
    end

    attr_accessor :l_space, :tail_space, :r_space

    def to_s
      s = "#{@l_space}<#{@end_slash}#{@name}"
      @attrs.each {|space, a_name, a_value| s << "#{space}#{a_name}=\"#{a_value}\"" }
      s << "#{@tail_space}#{@empty_slash}>#{@r_space}"
      return s
    end

  end


  class Element

    def initialize(stag, etag, children)
      @stag, @etag, @children = stag, etag, normalize(children)
    end

    attr_accessor :stag, :etag, :children

    def normalize(nodes)
      arr = []
      return arr unless nodes
      s = ''
      nodes.each do |node|
        case node
        when String
          s << node
        when Element
          arr << s unless s.empty?
          arr << node
          s = ''
        else
          raise "unreachable"
        end
      end
      arr << s unless s.empty?
      return arr
    end

  end


end
