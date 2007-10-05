###
### $Rev$
### $Release$
### $Copyright$
###


import sys, os, re
import kwartzite
import kwartzite.config as config
from kwartzite.parser import Parser
from kwartzite.parser.TextParser import TextParser
from kwartzite.parser.XmlParser import XmlParser
from kwartzite.translator import Translator
from kwartzite.translator.PythonTranslator import PythonTranslator
from kwartzite.translator.JavaTranslator import JavaTranslator
from kwartzite.util import build_values_from_filename, parse_name_pattern



class CommandOptionError(kwartzite.BaseError):
    pass



class Main(object):


    def __init__(self, sys_argv=None, stdout=None, stderr=None):
        self.stdout = stdout is None and sys.stdout or stdout
        self.stderr = stderr is None and sys.stderr or stderr
        if sys_argv is None:
            sys_argv = sys.argv
        self.command = os.path.basename(sys_argv[0])
        self.args = sys_argv[1:]
        self.defaults = {
            'action':     'compile',
            'parser':     'text',
            'translator': 'python',
        }


    def help(self):
        d = self.defaults
        command = self.command
        t = (
            "pyKwartzite - designer-friendly template engine",
            "Release: %s" % kwartzite.RELEASE,
            "Usage: %s [options] [template1 [template2...]]" % command,
            "Options:",
            "  -h, --help :  help",
            "  -v         :  version",
            "  -n         :  no exec",
            "  -q         :  quiet mode",
            "  -a action  :  action (compile/parse/names) (default '%s')" % d['action'],
            "  -p name    :  parser name (text/xml) (default '%s')" % d['parser'],
            "  -t name    :  translator name (python/java) (default '%s')" % d['translator'],
            "  -o file    :  output filename",
            "  -d dir     :  output directory",
            "",
            "Available properties are shown by '-ht' or '-hp':",
            "  $ %s -hp text      # show properties of TextParser" % command,
            "  $ %s -hp xml       # show properties of XmlParser" % command,
            "  $ %s -ht python    # show properties of PythonTranslator" % command,
            "  $ %s -ht java      # show properties of JavaTranslator" % command,
            "",
            "Option '-o' and '--classname' can contain the folowing patterns:",
            "  %f    filename  (ex. 'foo-bar-baz.html')",
            "  %x    extension (ex. 'html)'",
            "  %b    filename without extension     (ex. 'foo-bar-baz')",
            "  %u    basename replaced [^\w] to '_' (ex. 'foo_bar_baz')",
            "  %d    dirname   (ex. '/path/to/template')",
            "  %c    classname (ex. 'foo_bar_baz_html') (not available with '--classname')",
            "For example, '-o %u.py' results in 'foo_bar_baz.py'.",
            "Names are capitalized when upper case (ex. '%F' => 'FooBarBazHtml')",
            "",
        )
        return "\n".join(t)


    def property_descriptions(self, obj):
        buf = []
        buf.append("Available properties for %s class:\n" % obj.__class__.__name__)
        #for name, desc in obj._property_descriptions:
        for name, argtype, desc in obj._property_descriptions:
            value = getattr(obj, name, None)
            s = '--%s=%s' % (name, argtype)
            buf.append(' %-15s : %s (default %s)\n' % (s, desc, repr(value)))
        return ''.join(buf)


    def execute(self, args=None):
        ## parse command-line options
        if args is None:
            args = self.args
        options, properties, filenames = self._parse_args(args)
        self.options = options
        self.properties = properties

        ## debug
        if options.get('D'):
            def debug(msg): self.stderr.write("*** debug: " + msg)
        else:
            def debug(msg): pass
        debug("options=%s\n" % repr(options))
        debug("properties=%s\n" % repr(properties))
        debug("filenames=%s\n" % repr(filenames))

        ## help, version
        flag_help = options.get('h') or properties.get('help')
        if flag_help and not options.get('p') and not options.get('t'):
            self.stdout.write(self.help())
            return
        if options.get('v'):
            self.stdout.write(kwartzite.RELEASE + "\n")
            return

        ## action
        action = options.get('a', 'compile')
        if action not in ('compile', 'parse', 'names'):
            msg = "-a %s: unknown action (expected 'compile', 'parse', or 'names')."
            raise self._error(msg % action)

        ## parser
        parser_name = options.get('p') or self.defaults['parser']
        parser_class = self._find_parser_class(parser_name)
        if not parser_class:
            raise self._error("-p %s: unknown parser name." % parser_name)
        parser = parser_class(**properties)
        if flag_help and options.get('p'):
            self.stdout.write(self.property_descriptions(parser))
            return

        ## translator
        translator_name = options.get('t') or self.defaults['translator']
        translator_class = self._find_translator_class(translator_name)
        if not translator_class:
            raise self._error("-t %s: unknown translator name." % translator_name)
        translator = translator_class(**properties)
        if flag_help and options.get('t'):
            self.stdout.write(self.property_descriptions(translator))
            return

        ## output directory
        output_dir = options.get('d')
        if output_dir:
            if not os.path.exists(output_dir):
                raise self._error("-d %s: not found." % output_dir)
            if not os.path.isdir(output_dir):
                raise self._error("-d %s: not a directory." % output_dir)

        ## main loop
        noexec = options.get('n')
        quiet = options.get('q')
        if quiet:
            def report(msg): pass
        else:
            def report(msg): self.stderr.write(msg)
        if not filenames:
            filenames = [ None ]
        for filename in filenames:
            ## file check
            if not noexec:
                if not os.path.exists(filename):
                    raise self._error("%s: file not founnd." % filename)
                if not os.path.isfile(filename):
                    raise self._error("%s: not a file." % filename)
            ## input/output filename
            input_filename = filename or '(stdin)'
            output_filename = options.get('o')
            if not output_filename:
                output_filename = '-'
            elif filename and '%' in output_filename:
                pattern = output_filename
                values = build_values_from_filename(filename)
                classname = translator.build_classname(filename, properties.get('classname'))
                values['c'] = classname
                output_filename = parse_name_pattern(pattern, values)
            if output_dir:
                output_filename = '%s/%s' % (output_dir, output_filename)
            ## parse and translate a template
            if output_filename != '-':
                s = os.path.exists(output_filename) and 'updating' or 'creating'
                report("%s %s ... " % (s, output_filename))
            if not noexec:
                input = (filename and open(filename) or self.stdin).read()
                if action == 'compile':
                    template_info = parser.parse(input, input_filename)
                    output = translator.translate(template_info)
                elif action == 'parse':
                    template_info = parser.parse(input, input_filename)
                    output = template_info.inspect()
                elif action == 'names':
                    template_info = parser.parse(input, input_filename)
                    L = [ "%s:%d: %s\n" % (input_filename, e.stag_info.linenum, name)
                          for name, e in template_info.elem_info_table.iteritems() ]
                    output = ''.join(L)
                else:
                    assert "unreachable"
            ## output
            if not noexec:
                if output_filename == '-':
                    self.stdout.write(output)
                else:
                    open(output_filename, 'w').write(output)
            if output_filename != '-':
                report("done.\n")


    def _error(self, message):
        return CommandOptionError(message)


    def _find_parser_class(self, parser_name):
        parser_class_table = {
            'text': TextParser,
            #'html': HtmlParser,
            'xml':  XmlParser,
        }
        parser_class = parser_class_table.get(parser_name)
        if not parser_class:
            parser_class = globals().get(parser_name)
            if parser_class and not isinstance(parser_class, Parser):
                parser_class = None
        return parser_class


    def _find_translator_class(self, translator_name):
        translator_class_table = {
            'python': PythonTranslator,
            'java':   JavaTranslator,
            #'ruby':  RubyTranslator,
            #'php':   PhpTranslator,
            #'js':    JavascriptTranslator,
        }
        translator_class = translator_class_table.get(translator_name)
        if not translator_class:
            translator_class = globals().get(translator_name)
            if translator_class and not isinstance(translator_class, Translator):
                translator_class = None
        return translator_class


    def _parse_args(self, args, noarg="Dhnqv", required="adopt", optional=""):
        options = {}
        properties = {}
        i = 0
        n = len(args)
        while i < n and args[i] and args[i][0] == '-':
            arg = args[i]
            if arg == '-':
                i += 1
                break
            if arg[1] == '-':
                optstr = arg
                m = re.match('^--([-\w]+)(?:=(.*))?$', optstr)
                if not m:
                    raise sel._error("%s: invalid property." % optstr)
                name = m.group(1).replace('-', '_')
                val  = m.group(2)
                val  = val is None and True or self._to_value(val)
                properties[name] = val
            else:
                optstr = arg[1:]
                for (j, ch) in enumerate(optstr):
                    if ch in noarg:
                        options[ch] = True
                    elif ch in required:
                        optarg = optstr[j+1:]
                        if not optarg:
                            i += 1
                            if i == len(args):
                                raise self._error("-%s: argument required." % ch)
                            optarg = args[i]
                        options[ch] = optarg
                        break
                    elif ch in optional:
                        options[ch] = optstr[j+1:] or True
                        break
                    else:
                        raise self._error("-%s: unknown option." % ch)
            ## continue while-loop
            i += 1
        ## return
        filenames = args[i:]
        return (options, properties, filenames)


    def _to_value(self, val):
        if not isinstance(val, (str, unicode)): return val
        if val in ('true','True','yes'):  return True
        if val in ('false','False','no'): return False
        if val in ('null','None','nil'):  return None
        if re.match('^\d+$', val):        return int(val)
        if re.match('^\d+.\d+$', val):    return float(val)
        if re.match('^".*"$', val):       return val[1:-1]
        if re.match("^'.*'$", val):       return val[1:-1]
        return val



def main(sys_argv=None, stdout=None, stderr=None):
    if sys_argv is None: sys_argv = sys.argv
    try:
        Main(sys_argv, stdout=stdout, stderr=stderr).execute()
    except kwartzite.BaseError, ex:
        stderr = stderr is None and sys.stderr or stderr
        stderr.write(str(ex) + "\n")
        sys.exit(1)



if __name__ == "__main__":

    Main(sys.argv).execute()
