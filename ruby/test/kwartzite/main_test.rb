###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'
require 'cmdoptparser'

require 'kwartzite/main'
require 'kwartzite'


module Kwartzite


  class Main::TestCase
    include Oktest::TestCase

    def before
      @main = Main.new('rbkwartzite')
    end

    def test_run
      spec "if invalid command option specified then raises error." do
        pr = proc { @main.run(["-hvx"]) }
        ok {pr}.raise?(CommandOption::Error, "-x: unknown option.")
      end
      spec "if '-h' or '--help' specified then prints help message." do
        expected = HELP
        sout, serr = capture_io { @main.run(["-h"]) }
        ok {sout} == expected
        sout, serr = capture_io { @main.run(["--help"]) }
        ok {sout} == expected
      end
      spec "if '-v' or '--version' specified then prints version info." do
        expected = Kwartzite::VERSION + "\n"
        sout, serr = capture_io { @main.run(["-v"]) }
        ok {sout} == expected
        sout, serr = capture_io { @main.run(["--version"]) }
        ok {sout} == expected
      end
      fname = 'foo-bar-baz.html'
      pr = proc do |argv|
        capture_io do
          dummy_file(fname=>INPUT1) { @main.run(argv) }
        end
      end
      spec "'-l' specifies lang name." do
        sout, serr = pr.call(['-l', 'ruby', fname])
        ok {sout} == EXPECTED1
      end
      spec "'-p' specifies parser type." do
        sout, serr = pr.call(['-p', 'text', fname])
        ok {sout} == EXPECTED1
      end
      spec "'-c' specifies classname." do
        sout, serr = pr.call(['-c', '%B_HTML', fname])
        ok {sout} == EXPECTED1.gsub(/FooBarBazHtml_/, 'FooBarBaz_HTML')
      end
      spec "'-o' specifies output filename." do
        outfile = 'FooBarBazHtml_.rb'
        begin
          sout, serr = pr.call(['-o', '%C_.rb', fname])
          ok {sout} == ""
          ok {outfile}.exist?
        ensure
          File.unlink(outfile) if File.exist?(outfile)
        end
      end
      spec "converts files into class definitions." do
        # skip
      end
    end

    def test_SELF_main
      fname = 'foo-bar-baz.html'
      spec "runs Main object with ARGV." do
        argv = ["-c", "%C_", "-lruby", "-ptext", fname]
        sout, serr = capture_io do
          dummy_file fname=>INPUT1 do
            Main.main(argv, 'rbkwartzite')
          end
        end
        ok {sout} == EXPECTED1
      end
      spec "if command option is invalid then print error message to stderr." do
        argv = ["-x", "%C_", "-lruby", "-ptext", fname]
        sout, serr = capture_io do
          Main.main(argv, 'rbkwartzite')
        end
        ok {sout} == ""
        ok {serr} == "rbkwartzite: -x: unknown option.\n"
      end
    end

    HELP = <<'END'
rbKwartzite - pure html template engine for web application
Usage: rbkwartzite [..options..] file.html ...
  -h, --help     : show help
  -v, --version  : show version
  -l lang        : lang (ruby/python/java) (default: ruby)
  -p name        : parser name (text/html) (default: text)
  -c class       : class name format (default: %C_) (see below)
  -o file        : output filename format

Option '-c' and '-o' can contain the folowing patterns:
Format:
  %f    filename  (ex. 'foo-bar-baz.html')
  %x    extension (ex. 'html)'
  %b    filename without extension     (ex. 'foo-bar-baz')
  %u    basename replaced [^w] to '_' (ex. 'foo_bar_baz')
  %d    dirname   (ex. '/path/to/template')
  %c    classname (ex. 'foo_bar_baz_html') (not available with '--classname')
For example, '-o %u.py' results in 'foo_bar_baz.py'.
Names are capitalized when upper case (ex. '%F' => 'FooBarBazHtml')

Examples:
  # ex.1 convert a html file into Ruby class
  $ rbkwartzite -c '%BHtml_' foo-bar.html > FooBarHTML_.rb
  $ ruby FooBar_HTML.rb   # optional
  # ex.2 convert html files in a directory
  $ rbkwartzite -c '%C_' html/*.html -o 'ruby/%C_.rb'
  # ex.3 convert html files into Java classes
  $ rbkwartzite -c '%C_' -l java html/*.html -o 'java/%C_.java'
END

    INPUT1 = <<'END'
<ul>
  <li data-kwd="mark:item">foo</li>
</ul>
END

    EXPECTED1 = <<'END'
##
## generated from foo-bar-baz.html by rbKwartzite
##

require 'kwartzite/html'


class FooBarBazHtml_ < Kwartzite::HtmlTemplate

  def elem_DOCUMENT()
    @_buf << %Q`<ul>\n`
    elem_item()
    @_buf << %Q`</ul>\n`
  end

  ######## mark:item ########

  def elem_item(attrs=nil)
    stag_item(attrs)
    cont_item()
    etag_item()
  end

  def attr_item()
    @attr_item ||= {
    }
  end

  def stag_item(attrs=nil)
    if attrs.nil?
      @_buf << %Q`  <li>`
    else
      @_buf << %Q`  <li`
      attr_item().merge(attrs).each_pair do |k, v|
        @_buf << %Q` #{k}="#{escape(v)}"` unless v.nil?
      end
      @_buf << %Q`>`
    end
  end

  def cont_item()
    @_buf << %Q`foo`
  end

  def etag_item()
    @_buf << %Q`</li>\n`
  end

end


if __FILE__ == $0
  print FooBarBazHtml_.new.render
end
END

  end


end
