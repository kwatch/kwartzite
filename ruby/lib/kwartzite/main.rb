###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'cmdoptparser'


module Kwartzite


  class Main

    def initialize(command=nil)
      @command = command || File.basename($0)
    end

    attr_accessor :command

    def cmdopt_parser()
      parser = CommandOption::Parser.new
      parser.option("-h", "--help").desc("show help")
      parser.option("-v", "--version").desc("show version")
      parser.option("-l").name('lang').arg("lang", :default=>'ruby')\
                         .desc("lang (ruby/python/java) (default: ruby)")
      #parser.option("-q").desc("quiet mode")
      parser.option("-p").name('parser').arg("name")\
                         .desc("parser name (text/html) (default: text)")
      parser.option("-c").name('classname').arg("class")\
                         .desc("class name format (default: %C_) (see below)")
      parser.option("-o").name('outfile').arg("file")\
                         .desc("output filename format")
      parser.option("-d").name('outdir').arg("dir")#\
                         #.desc("output directory")
      return parser
    end

    def run(argv=ARGV)
      parser = cmdopt_parser()
      cmdopt, filenames = parser.parse(argv)
      if cmdopt.help
        help(parser)
        return
      end
      if cmdopt.version
        puts Kwartzite::VERSION
        return
      end
      #
      opts = {}
      opts[:lang]      = cmdopt.lang || 'ruby'
      opts[:parser]    = cmdopt.parser || 'text'
      opts[:classname] = cmdopt.classname if cmdopt.classname
      opts[:outfile]   = cmdopt.outfile if cmdopt.outfile
      opts[:outdir]    = cmdopt.outdir  if cmdopt.outdir
      #
      director = Director.new(opts)
      filenames.each do |filename|
        output = director.construct(filename)
        print output unless opts[:outfile]
      end
    end

    def help(cmdopt_parser)
      puts "rbKwartzite - pure html template engine for web application"
      puts "Usage: #{@command} [..options..] file.html ..."
      puts cmdopt_parser.options_help(:width=>15)
      puts <<END

Option '-c' and '-o' can contain the folowing patterns:
Format:
  %f    filename  (ex. 'foo-bar-baz.html')
  %x    extension (ex. 'html)'
  %b    filename without extension     (ex. 'foo-bar-baz')
  %u    basename replaced [^\w] to '_' (ex. 'foo_bar_baz')
  %d    dirname   (ex. '/path/to/template')
  %c    classname (ex. 'foo_bar_baz_html') (not available with '--classname')
For example, '-o %u.py' results in 'foo_bar_baz.py'.
Names are capitalized when upper case (ex. '%F' => 'FooBarBazHtml')

Examples:
  # ex.1 convert a html file into Ruby class
  $ #{@command} -c '%B_HTML' foo-bar.html > FooBar_HTML.rb
  $ ruby FooBar_HTML.rb   # optional
  # ex.2 convert html files into Java class
  $ #{@command} -c '%B_HTML' -l java foo-bar.html > FooBar_HTML.java
  # ex.3 convert html files in a directory
  $ #{@command} -c '%B_HTML' html/*.html -o 'ruby/%B_HTML.rb'
END
    end

    def self.main
      main = self.new
      begin
        main.run(ARGV)
      rescue CommandOption::Error => ex
        $stderr.puts "#{main.command}: #{ex.message}"
      end
    end

  end


end
