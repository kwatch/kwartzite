###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module Kwartzite


  DIRECTIVE_ATTR = 'data-kwd'


  class Parser

    def initialize(opts={})
      #: set @d_attr.
      #: if :d_attr is not passed then use DIRECTIVE_ATTR instead.
      @d_attr = opts[:d_attr] || DIRECTIVE_ATTR
    end

    attr_accessor :d_attr

    def parse_file(filename)
      #: read file and pass it to parse().
      return parse(File.open(filename, 'rb').read, filename)
    end

    def parse(input, filename='(unknown)')
      # abstract
    end

    @registered = {}

    def self.register(lang, klass)
      #: regsiter klass with lang.
      @registered[lang] = klass
    end

    def self.get_class(lang)
      #: return klass object registered with lang.
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
      #: return true if start-tag.
      @kind == :stag
    end

    def etag?
      #: return true if end-tag.
      @kind == :etag
    end

    def empty?
      #: return true if empty-tag.
      @kind == :empty
    end

    def set_directive(directive)
      #: set directive value.
      @directive = directive
      #: return self.
      return self
    end

    def has_directive?
      #: return true if directive is set.
      !! @directive
    end

    attr_accessor :directive

    def set_spaces(l_space, tail_space, r_space)
      #: set left-space, tail-space, and right-space.
      @l_space, @tail_space, @r_space = l_space, tail_space, r_space
      #: return self.
      return self
    end

    attr_accessor :l_space, :tail_space, :r_space

    def to_s
      #: return html tag string.
      s = "#{@l_space}<#{@end_slash}#{@name}"
      @attrs.each {|space, a_name, a_value| s << "#{space}#{a_name}=\"#{a_value}\"" }
      s << "#{@tail_space}#{@empty_slash}>#{@r_space}"
      return s
    end

  end


  class Element

    def initialize(stag, etag, children)
      #: normalize child nodes.
      @stag, @etag, @children = stag, etag, normalize(children)
    end

    attr_accessor :stag, :etag, :children

    protected

    def normalize(nodes)
      #: concat sequencial strings in nodes into a string.
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


  class ParseError < SyntaxError
  end


end
