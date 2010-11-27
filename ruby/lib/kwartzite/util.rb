###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module Kwartzite


  module Util

    class Cycle

      def initialize(*values)
        @values = values
        @count = @values.length
        @index = -1
      end

      def value
        @index += 1
        @index = 0 if @index == @cout
        return @values[@index]
      end

      alias to_s value

    end

    module_function

    def name_format(format, filename)
      base = File.basename(filename)
      return format.gsub(/%(.)/) do
        ch = $1
        case ch
        when '%' ;  '%'
        when 'f' ;  base
        when 'x' ;  File.extname(base)[1..-1]
        when 'b' ;  base.split(/\./, 2).first
        when 'u' ;  base.split(/\./, 2).first.gsub(/[^\w]/, '_')
        when 'd' ;  File.dirname(filename)
        when 'c' ;  base.gsub(/[^\w]/, '_')
        when 'F' ;  _camelcase base
        when 'X' ;  _camelcase File.extname(base)[1..-1]
        when 'B' ;  _camelcase base.split(/\./, 2).first
        when 'U' ;  _camelcase base.split(/\./, 2).first.gsub(/[^\w]/, '_')
        when 'D' ;  _camelcase File.dirname(filename)
        when 'C' ;  _camelcase base.gsub(/[^\w]/, '_')
        else
          raise ArgumentError.new("%#{ch}: unknown format for class name.")
        end
      end
    end

    def _camelcase(str)
      str.split(/[^a-zA-Z0-9]/).collect {|x| x.capitalize }.join
    end

  end


end
