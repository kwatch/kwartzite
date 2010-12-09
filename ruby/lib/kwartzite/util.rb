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

      attr_reader :values

      def value
        #: returns next value cyclicly.
        @index += 1
        @index = 0 if @index == @count
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
        #: '%%' -> '%'.
        when '%' ;  '%'
        #: '%f' -> 'foo-bar.html'.
        when 'f' ;  base
        #: '%x' -> 'html'.
        when 'x' ;  File.extname(base)[1..-1]
        #: '%b' -> 'foo-bar'.
        when 'b' ;  base.split(/\./, 2).first
        #: '%u' -> 'foo_bar'.
        when 'u' ;  base.split(/\./, 2).first.gsub(/[^\w]/, '_')
        #: '%d' -> 'some/where'.
        when 'd' ;  File.dirname(filename)
        #: '%c' -> 'foo_bar_html'.
        when 'c' ;  base.gsub(/[^\w]/, '_')
        #: '%F' -> 'FooBarHtml'.
        when 'F' ;  _camelcase base
        #: '%X' -> 'Html'.
        when 'X' ;  _camelcase File.extname(base)[1..-1]
        #: '%B' -> 'FooBar'.
        when 'B' ;  _camelcase base.split(/\./, 2).first
        #: '%U' -> 'FooBar'.
        when 'U' ;  _camelcase base.split(/\./, 2).first.gsub(/[^\w]/, '_')
        #: '%D' -> 'SomeWhere'.
        when 'D' ;  _camelcase File.dirname(filename)
        #: '%C' -> 'FooBarHtml'.
        when 'C' ;  _camelcase base.gsub(/[^\w]/, '_')
        #: raises error when unknown format character.
        else
          raise ArgumentError.new("%#{ch}: unknown format for class name.")
        end
      end
    end

    def _camelcase(str)   # :nodoc:
      #: 'foo-bar.html' -> 'FooBarHtml'
      str.split(/[^a-zA-Z0-9]/).collect {|x| x.capitalize }.join
    end

  end


end
