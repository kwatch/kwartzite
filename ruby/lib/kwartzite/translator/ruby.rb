###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'kwartzite/translator'


module Kwartzite


  class RubyTranslator < Translator
    Translator.register('ruby', self)

    def translate(nodes, opts={})
      opts.update(@opts)
      filename = opts[:filename]
      classname = Util.name_format(opts[:classname] || '%C_', filename)
      baseclass = Util.name_format(opts[:baselass] || 'Kwartzite::HtmlTemplate', filename)
      @buf = buf = ""
      print_header(opts, filename, classname)
      @buf <<   "class #{classname} < #{baseclass}\n"
      @buf <<   "\n"
      #
      @buf <<   "  def elem_DOCUMENT()\n"
      translate_nodes(nodes)
      @buf <<   "  end\n"
      @buf <<   "\n"
      #
      nodes.each do |node|
        next unless node.is_a?(Element)
        define_element(node)
      end
      #
      @buf <<   "end\n"
      print_footer(opts, filename, classname)
      return buf
    end

    def print_header(opts, filename, classname)
      @buf <<   "##\n"
      @buf <<   "## generated from #{filename} by rbKwartzite\n"
      @buf <<   "##\n"
      @buf <<   "\n"
      @buf <<   "require 'kwartzite/html'\n"
      @buf <<   "\n"
      print_moduledefs(opts, classname)
    end

    def print_moduledefs(opts, classname)
      mod_names = classname.split(/::/)[0...-1]
      mod_names.each_with_index do |mod_name, i|
        @buf << ("  " * i) << "module #{mod_name}\n"
      end
      (mod_names.length - 1).downto(0) do |i|
        s = i == 0 ? " unless defined?(#{mod_names.join('::')})" : nil
        @buf << ("  " * i) << "end#{s}\n"
      end
      @buf <<   "\n"
    end

    def print_footer(opts, filename, classname)
      @buf <<   "\n"
      @buf <<   "\n"
      @buf <<   "if __FILE__ == $0\n"
      @buf <<   "  print #{classname}.new.render\n"
      @buf <<   "end\n"
    end

    def translate_nodes(nodes)
      nodes.each do |node|
        case node
        when String  ;  translate_string(node)
        when Element ;  translate_element(node)
        else         ;  raise "unreachabled"
        end
      end
    end

    def translate_string(text)
      @buf <<   "    @_buf << #{convert_text(text)}\n"
    end

    def _escape_text(text)
      return text.gsub(/[`\\]/, '\\\\\&')
    end

    def _crlf(str)
      return str.sub(/\r?\n\z/) { $& == "\n" ? "\\n" : "\\r\\n" }
    end

    def convert_text(text)
      s = _escape_text(text)
      s = _crlf(s)
      return "%Q`#{s}`"
    end

    def translate_element(elem)
      case elem.stag.directive
      when /\Amark:(.*)\z/  ; translate_directive_mark(elem, $1)
      when /\Avalue:(.*)\z/ ; translate_directive_value(elem, $1)
      when /\Arawvalue:(.*)\z/ ; translate_directive_rawvalue(elem, $1)
      when /\Adummy:(.*)\z/ ; translate_directive_dummy(elem, $1)
      #when /\A(\w+)\z/      ; translate_directive_mark(elem, $1)
      else
        raise "error: unsupported directive: #{elem.stag.directive}"
      end
    end

    def translate_directive_mark(elem, arg)
      @buf <<   "    elem_#{arg}()\n"
    end

    def translate_directive_value(elem, arg)
      translate_directive_rawvalue(elem, common_expression(arg))
    end

    def translate_directive_rawvalue(elem, arg)
      value = arg
      tag = elem.stag
      remove_p = tag.name == 'span' && tag.attrs.empty?
      if remove_p
        @buf << "    @_buf << #{@escapefunc}(#{value})\n"
      else
        s = ''
        s << _escape_text(elem.stag.to_s)
        s << "\#{#{@escapefunc}(#{value})}"
        s << _escape_text(elem.etag.to_s)
        s = _crlf(s)
        @buf << "    @_buf << %Q`#{s}`\n"
      end
    end

    def translate_directive_dummy(elem, arg)
      # ignore
    end

    def common_expression(expr)
      s = ''
      case expr
      when /\A[a-z_]\w*(\.[a-z_]\w*(\(\))?|\[('[^']*'|"[^"]*"|:\w+|\w+)\])*\z/
        return "@#{expr}"
      else
        return expr
      end
    end

    def define_element(elem)
      directive = elem.stag.directive
      if directive =~ /\Amark:(.*)\z/
        mark = $1
        define_elem(elem, mark);  @buf << "\n"
        define_attr(elem, mark);  @buf << "\n"
        define_stag(elem, mark);  @buf << "\n"
        define_cont(elem, mark);  @buf << "\n"
        define_etag(elem, mark);  @buf << "\n"
      end
      elem.children.each do |node|
        define_element(node) if node.is_a?(Element)
      end
    end

    def define_elem(elem, mark)
      @buf <<   "  ######## mark:#{mark} ########\n"
      @buf <<   "\n"
      @buf <<   "  def elem_#{mark}()\n"
      @buf <<   "    stag_#{mark}()\n"
      @buf <<   "    cont_#{mark}()\n"
      @buf <<   "    etag_#{mark}()\n"
      @buf <<   "  end\n"
    end

    def define_attr(elem, mark)
      @buf <<   "  def attr_#{mark}()\n"
      @buf <<   "    @attr_#{mark} ||= {\n"
      elem.stag.attrs.each do |space, a_name, a_value|
        @buf << "      :#{a_name} => SafeStr.new(#{a_value.inspect}),\n"
      end
      @buf <<   "    }\n"
      @buf <<   "  end\n"
    end

    def define_stag(elem, mark)
      @buf <<   "  def stag_#{mark}(attrs=nil)\n"
      @buf <<   "    if attrs.nil?\n"
      @buf <<   "      @_buf << %Q`#{_crlf(_escape_text(elem.stag.to_s))}`\n"
      @buf <<   "    else\n"
      @buf <<   "      @_buf << %Q`#{elem.stag.l_space}<#{elem.stag.name}`\n"
      @buf <<   "      attr_#{mark}().merge(attrs).each_pair do |k, v|\n"
      @buf <<   "        @_buf << %Q` \#{k}=\"\#{#{@escapefunc}(v)}\"` unless v.nil?\n"
      @buf <<   "      end\n"
      @buf <<   "      @_buf << %Q`>#{_crlf(elem.stag.r_space.to_s)}`\n"
      @buf <<   "    end\n"
      @buf <<   "  end\n"
    end

    def define_cont(elem, mark)
      @buf <<   "  def cont_#{mark}()\n"
      translate_nodes(elem.children)
      @buf <<   "  end\n"
    end

    def define_etag(elem, mark)
      @buf <<   "  def etag_#{mark}()\n"
      @buf <<   "    @_buf << %Q`#{_crlf(elem.etag.to_s)}`\n" if elem.etag
      @buf <<   "  end\n"
    end

  end


end
