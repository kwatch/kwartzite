###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module Kwartzite


  class Director

    DEFAULTS = {
      :classname  => '%C_',
      :encoding   => nil,
      :baseclass  => 'Kwartzite::HtmlTemplate',
      :lang       => 'ruby',
      :parser     => 'text',
      :escapefunc => 'escape',
      :outfile    => nil,
    }

    def initialize(opts={})
      @opts = opts.merge(DEFAULTS)
      @parser = _get_parser(@opts)
      @translator = _get_translator(@opts)
    end

    def construct(filename, opts={})
      opts.merge(@opts)
      opts[:filename] = filename
      input = opts[:input] || File.open(filename, 'rb') {|f| f.read }
      nodes = @parser.parse(input, filename)
      output = @translator.translate(nodes, opts)
      if opts[:outfile]
        outfile = Util.name_format(opts[:outfile], filename)
        File.open(outfile, 'wb') {|f| f.write(output) }
      end
      return output
    end

    private

    def _get_object(base_klass, arg, opts)
      return arg if arg.is_a?(base_klass)
      return arg.new(opts) if arg.is_a?(Class) && arg < base_klass
      klass = base_klass.get_class(arg)
      return klass.new(opts) if klass
      return nil
    end

    def _get_parser(opts)
      parser = _get_object(Parser, opts[:parser], opts)  or
        raise ArgumentError.new("#{opts[:parser].inspect}: unknown parser.")
      return parser
    end

    def _get_translator(opts)
      translator = _get_object(Translator, opts[:lang], opts)  or
        raise ArgumentError.new("#{opts[:lang].inspect}: unknown lang.")
      return translator
    end

  end


end
