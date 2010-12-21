###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'kwartzite/translator'
require 'kwartzite/util'


module Kwartzite


  class PythonTranslator < Translator
    Translator.register('python', self)

    DEFAULTS = Translator::DEFAULTS.dup.merge({
      :baseclass => 'kwartzite.html.HtmlTemplate',
      :escape    => 'self.escape',
    })

    def translate(nodes, opts={})
      opts = @opts.merge(opts)
      filename = opts[:filename]
      #: accepts opts[:classname].
      classname = Util.name_format(opts[:classname], filename)
      #: accepts opts[:baseclass].
      baseclass = Util.name_format(opts[:baseclass], filename)
      @buf = ""
      print_header(opts, filename, classname)
      @buf <<   "class #{classname}(#{baseclass}):\n"
      @buf <<   "\n"
      #
      @buf <<   "    def elem_DOCUMENT(self):\n"
      translate_nodes(nodes)
      @buf <<   "\n"
      #
      nodes.each do |node|
        next unless node.is_a?(Element)
        define_element(node)
      end
      #
      print_footer(opts, filename, classname)
      #: returns source code of Python class.
      return @buf
    end

    protected

    def print_header(opts, filename, classname)
      @buf <<   "##\n"
      @buf <<   "## generated from #{filename} by rbKwartzite\n"
      @buf <<   "##\n"
      @buf <<   "\n"
      @buf <<   "import kwartzite\n"
      @buf <<   "from kwartzite import SafeStr\n"
      @buf <<   "\n"
      print_moduledefs(opts, classname)
    end

    def print_moduledefs(opts, classname)
      @buf <<   "\n"
    end

    def print_footer(opts, filename, classname)
      @buf <<   "\n"
      @buf <<   "\n"
      @buf <<   "if __name__ == '__main__':\n"
      @buf <<   "    import sys\n"
      @buf <<   "    sys.stdout.write(#{classname}().render())\n"
      @buf <<   "\n"
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
      @buf <<   "        self._buf.append(#{convert_text(text)})\n"
    end

    def q(str)
      "'#{str.gsub(/'/, '\\\\\&')}'"
    end

    def quote(str, escape_crlf=false)
      s = _escape_text(str)
      s = _crlf(s) if escape_crlf
      "'''#{s}'''"
    end

    def _escape_text(text)
      return text.gsub(/['\\]/, '\\\\\&')
    end

    def _crlf(str)
      return str.sub(/\r?\n\z/) { $& == "\n" ? "\\n" : "\\r\\n" }
    end

    def convert_text(text)
      s = _escape_text(text)
      s = _crlf(s)
      return "'''#{s}'''"
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
      @buf <<   "        self.elem_#{arg}()\n"
    end

    def translate_directive_value(elem, arg)
      translate_directive_rawvalue(elem, common_expression(arg))
    end

    def translate_directive_rawvalue(elem, arg)
      value = arg
      tag = elem.stag
      remove_p = tag.name == 'span' && tag.attrs.empty?
      cont = "#{@escapefunc}(#{value})"
      if remove_p
        #@buf << "        self._buf.append(#{cont})\n"
        @buf << "        self.echo(#{cont})\n"
      else
        stag = quote(elem.stag.to_s)
        etag = quote(elem.etag.to_s, true)
        #@buf << "        self._buf.extend((#{stag}, #{cont}, #{etag}))\n"
        @buf << "        self._buf.append(#{stag})\n"
        @buf << "        self.echo(#{cont})\n"
        @buf << "        self._buf.append(#{etag})\n"
      end
    end

    def translate_directive_dummy(elem, arg)
      # ignore
    end

    def common_expression(expr)
      s = ''
      case expr
      when /\A[a-z_]\w*(\.[a-z_]\w*(\(\))?|\[('[^']*'|"[^"]*"|:\w+|\w+)\])*\z/
        return "self.#{expr}"
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
      @buf <<   "    ######## mark:#{mark} ########\n"
      @buf <<   "\n"
      @buf <<   "    def elem_#{mark}(self, attrs=None):\n"
      @buf <<   "        self.stag_#{mark}(attrs)\n"
      @buf <<   "        self.cont_#{mark}()\n"
      @buf <<   "        self.etag_#{mark}()\n"
      @buf <<   "    _elem_#{mark} = elem_#{mark}\n"
    end

    def define_attr(elem, mark)
      @buf <<   "    attr_#{mark} = {\n"
      elem.stag.attrs.each do |space, a_name, a_value|
        @buf << "        #{q(a_name)}: SafeStr(#{q(a_value)}),\n"
      end
      @buf <<   "    }\n"
    end

    def define_stag(elem, mark)
      @buf <<   "    def stag_#{mark}(self, attrs=None):\n"
      @buf <<   "        if attrs is None:\n"
      @buf <<   "            self._buf.append(#{quote(elem.stag.to_s, true)})\n"
      @buf <<   "        else:\n"
      @buf <<   "            self._buf.append('''#{elem.stag.l_space}<#{elem.stag.name}''')\n"
      @buf <<   "            dct = self.attr_#{mark}.copy()\n"
      @buf <<   "            dct.update(attrs)\n"
      @buf <<   "            for k, v in dct.iteritems():\n"
      @buf <<   "                if v is not None:\n"
      @buf <<   "                    self._buf.extend((' ', k, '=\"', #{@escapefunc}(v), '\"'))\n"
      @buf <<   "            self._buf.append('''#{elem.stag.tail_space}#{elem.stag.empty_slash}>#{_crlf(elem.stag.r_space.to_s)}''')\n"
      @buf <<   "    _stag_#{mark} = stag_#{mark}\n"
    end

    def define_cont(elem, mark)
      @buf <<   "    def cont_#{mark}(self):\n"
      translate_nodes(elem.children)
      @buf <<   "    _cont_#{mark} = cont_#{mark}\n"
    end

    def define_etag(elem, mark)
      s = quote(elem.etag.to_s, true)
      @buf <<   "    def etag_#{mark}(self):\n"
      @buf <<   "        self._buf.append(#{s})\n" if elem.etag
      @buf <<   "        pass\n"                   if ! elem.etag
      @buf <<   "    _etag_#{mark} = etag_#{mark}\n"
    end

  end


end
