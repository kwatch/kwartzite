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
      tag_rexp, attr_rexp = TAG_REXP, ATTR_REXP
      @input.scan(tag_rexp) do
        m = Regexp.last_match
        string, l_space, end_slash, tag_name, attr_str, tail_space, empty_slash, r_space = m.to_a
        attrs = []
        attr_str.scan(attr_rexp) do |space, a_name, a_value|
          a_value = a_value =~ /\A"(.*)"\z/ ? $1 : a_value
          attrs << [space, a_name, a_value]
        end if attr_str
        directive = _get_directive(attrs)
        kind = nil
        if end_slash == '/'
          kind = :etag  if tag_name == nested_tag_name
        elsif empty_slash == '/'
          kind = :empty if directive
        else
          kind = :stag if directive || tag_name == nested_tag_name
          kind = :empty if kind && empty_tag_name?(tag_name)
        end
        if kind
          @text  = @input[0, m.begin(0)]
          @input = @input[m.end(0)..-1]
          tag =  Tag.new(kind, tag_name, attrs, m[0]) \
                    .set_directive(directive) \
                    .set_spaces(l_space, tail_space, r_space)
          tag.empty_slash = nil unless empty_slash == '/'
          return tag
        end
        pos = m.end(0)
      end
      @text = @input
      @input = nil
      return nil
    end

    def _get_directive(attrs)
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

    def empty_tag_name?(tag_name)
      EMPTY_TAG_NAMES_DICT.key?(tag_name)
    end

  end


  class TextParser < Parser
    Parser.register('text', self)

    def parse(input, filename='(unknown)')
      scanner = TextScanner.new(input, filename, @directive_attr)
      elem = parse_elem(scanner, nil)
      nodes = elem.children
      return nodes
    end

    def parse_elem(scanner, start_tag)
      tag_name = start_tag ? start_tag.name : nil
      children = []
      while (tag = scanner.scan_tag(tag_name))
        text = scanner.text
        children << text unless text.empty?
        kind = tag.kind
        if kind == :stag
          elem = parse_elem(scanner, tag)
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
      if start_tag
        raise ParseError.new("tag '<#{start_tag.name}>' is not closed.")
      end
      scanner.input.nil?  or raise "assertion error"
      children << scanner.text
      return Element.new(nil, nil, children)
    end

  end


end
