###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'kwartzite/parser'


module Kwartzite


  class TextScanner

    name_pat  = '[a-zA-Z][-\w]*(?::[-\w]+)*'
    value_pat = '"[^"]*"|\w+'
    TAG_REXP  = /(^[ \t]*)?<(\/)?(#{name_pat})((?:\s+#{name_pat}=(?:#{value_pat}))*)(\s*)(\/)?>([ \t]*\r?\n)?/
    ATTR_REXP = /(\s+)(#{name_pat})=(#{value_pat})/

    def initialize(input, filename=nil, directive_attr='data-kwd')
      @input = input
      @filename = nil
      @directive_attr = directive_attr
      @text = nil
    end

    attr_accessor :input, :filename, :directive_attr, :text

    def scan_tag(nested_tag_name)
      #: scans tags.
      tag_rexp, attr_rexp = TAG_REXP, ATTR_REXP
      @input.scan(tag_rexp) do
        m = Regexp.last_match
        string, l_space, end_slash, tag_name, attr_str, tail_space, empty_slash, r_space = m.to_a
        #: gets attributes.
        attrs = []
        attr_str.scan(attr_rexp) do |space, a_name, a_value|
          a_value = a_value =~ /\A"(.*)"\z/ ? $1 : a_value
          attrs << [space, a_name, a_value]
        end if attr_str
        #: gets directive string.
        directive = _get_directive(attrs)
        #: skips end tag if tag name is not equal to nested tag name.
        kind = nil
        if end_slash == '/'
          kind = :etag  if tag_name == nested_tag_name
        #: skips empty tag if it doesn't have directive.
        elsif empty_slash == '/'
          kind = :empty if directive
        #: skips start tag if no directives.
        #: skips start tag if not nested tag name.
        else
          kind = :stag if directive || tag_name == nested_tag_name
          #: regards '<input>', '<br>', ... as empty tag forcedly.
          kind = :empty if kind && empty_tag_name?(tag_name)
        end
        #: if tag found then returns it.
        #: text before tag is kept in @text.
        if kind
          @text  = @input[0, m.begin(0)]
          @input = @input[m.end(0)..-1]
          tag =  Tag.new(kind, tag_name, attrs, m[0]) \
                    .set_directive(directive) \
                    .set_spaces(l_space, tail_space, r_space)
          #: clears empty_slash of tag object if empty_slash is not specified.
          tag.empty_slash = nil unless empty_slash == '/'
          return tag
        end
        pos = m.end(0)
      end
      #: rest text is kept in @text.
      @text = @input
      @input = nil
      #: returns nil if reached to end of input string.
      return nil
    end

    private

    def _get_directive(attrs)   # :nodoc:
      d_attr = @directive_attr
      i = -1
      attrs.each_with_index do |a, j|
        break (i = j) if a[1] == d_attr
      end
      directive = nil
      if i >= 0
        directive = attrs.delete_at(i)[2]
        if directive.to_s.empty?
          directive = nil
        elsif directive =~ /\A\"(.*)"\z/
          directive = $1
        end
      end
      return directive
    end

    EMPTY_TAG_NAMES_DICT = {
      'input'=>true, 'img'=>true, 'br'=>true, 'hr'=>true, 'meta'=>true, 'link'=>true,
    }

    def empty_tag_name?(tag_name)  # :nodoc:
      #: returns true if tag_name is one of 'input', 'img', 'br', 'hr', 'meta', and 'link'.
      EMPTY_TAG_NAMES_DICT.key?(tag_name)
    end

  end


  class TextParser < Parser
    Parser.register('text', self)

    def parse(input, filename='(unknown)')
      #: returns nodes.
      #: raises ParseError if start-tag is not closed by corresponding end-tag.
      scanner = TextScanner.new(input, filename, @d_attr)
      elem = _parse_elem(scanner, nil)
      nodes = elem.children
      return nodes
    end

    private

    def _parse_elem(scanner, start_tag)  # :nodoc:
      tag_name = start_tag ? start_tag.name : nil
      children = []
      while (tag = scanner.scan_tag(tag_name))
        text = scanner.text
        children << text unless text.empty?
        kind = tag.kind
        if kind == :stag
          elem = _parse_elem(scanner, tag)
          if tag.has_directive?
            children << elem
          else
            children << elem.stag.string
            children.concat(elem.children)
            children << elem.etag.string
          end
        elsif kind == :empty
          tag.has_directive?  or raise "assertion failed"
          children << Element.new(tag, nil, nil)
        elsif kind == :etag
          end_tag = tag
          return Element.new(start_tag, end_tag, children)
        end
      end
      start_tag.nil?  or
        raise ParseError.new("tag '<#{start_tag.name}>' is not closed.")
      scanner.input.nil?  or raise "assertion failed"
      children << scanner.text
      return Element.new(nil, nil, children)
    end

  end


end
