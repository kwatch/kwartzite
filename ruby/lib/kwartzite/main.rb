###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'cmdoptparser'

require 'kwartzite/director'


module Kwartzite


  class Main

    def initialize(command=nil)
      @command = command || File.basename($0)
    end

    attr_accessor :command

    def _cmdopt_parser()
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
      return parser
    end
    private :_cmdopt_parser

    def run(argv=ARGV)
      parser = _cmdopt_parser()
      #: if invalid command option specified then raises error.
      cmdopt, filenames = parser.parse(argv)
      #: if '-h' or '--help' specified then prints help message.
      if cmdopt.help
        _help(parser)
        return
      end
      #: if '-v' or '--version' specified then prints version info.
      if cmdopt.version
        puts Kwartzite::VERSION
        return
      end
      #: '-l' specifies lang name.
      opts = {}
      opts[:lang]      = cmdopt.lang if cmdopt.lang
      #: '-p' specifies parser type.
      opts[:parser]    = cmdopt.parser if cmdopt.parser
      #: '-c' specifies classname.
      opts[:classname] = cmdopt.classname if cmdopt.classname
      #: '-o' specifies output filename.
      opts[:outfile]   = cmdopt.outfile if cmdopt.outfile
      #: converts files into class definitions.
      director = Director.new(opts)
      filenames.each do |filename|
        output = director.construct(filename)
        print output unless opts[:outfile]
      end
    end

    def _help(cmdopt_parser)
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
  $ #{@command} -c '%BHtml_' foo-bar.html > FooBarHTML_.rb
  $ ruby FooBar_HTML.rb   # optional
  # ex.2 convert html files in a directory
  $ #{@command} -c '%C_' html/*.html -o 'ruby/%C_.rb'
  # ex.3 convert html files into Java classes
  $ #{@command} -c '%C_' -l java html/*.html -o 'java/%C_.java'
END
    end
    private :_help

    def self.main(argv=ARGV, *args)
      #: runs Main object with ARGV.
      main = self.new(*args)
      begin
        main.run(argv)
      #: if command option is invalid then print error message to stderr.
      rescue CommandOption::Error => ex
        $stderr.puts "#{main.command}: #{ex.message}"
      end
    end

  end


end
