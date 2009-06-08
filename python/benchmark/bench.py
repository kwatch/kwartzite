# -*- coding: utf-8 -*-
import sys, os, re, time, getopt, marshal, fnmatch
from StringIO import StringIO
from glob import glob


## defaults
ntimes = 1000
quiet  = False
mode   = 'class'   # 'class' or 'dict'
targets_default = "\
tenjin tenjin-nocache tenjin-reuse \
kwartzite kwartzite-nocache kwartzite2 kwartzite2-nocache \
django django-reuse \
cheetah cheetah-reuse \
myghty myghty-reuse \
kid kid-reuse".split(' ')
targets_all = "\
tenjin-tmpl tenjin-scriptcache tenjin-bytecodecache tenjin-nocache tenjin-reuse tenjin-defun \
django django-reuse \
cheetah cheetah-reuse \
myghty myghty-reuse \
kid kid-reuse".split(' ')


## helper methods
def msg(message):
    if not quiet:
        sys.stdout.write(message)
        sys.stdout.flush()

def do_with_report(title, do_func):
    msg(title)
    msg(' ... ')
    start_t = time.time()
    ret = do_func()
    end_t = time.time()
    msg('done. (%f sec)\n' % (end_t - start_t))
    return ret

def import_module(name):
    try:
        return do_with_report('import %s' % name, lambda: __import__(name))
    except ImportError, ex:
        msg("\n")
        msg("*** module %s not found.\n" % name)
        raise ex

def is_required(name):
    global targets
    for t in targets:
        if t.startswith(name):
            return True
    return False

def has_metachar(s):
    return re.search(r'[*?]', s) is not None


def remove_file(*filenames):
    for filename in filenames:
        if os.path.isfile(filename):
            os.unlink(filename)


## parse options
try:
    optlist, targets = getopt.getopt(sys.argv[1:], "hpf:n:t:x:Aqm:k:e:l:")
    options = dict([(key[1:], val == '' and True or val) for key, val in optlist])
except Exception, ex:
    sys.stderr.write(str(ex) + "\n")
    sys.exit(1)
#sys.stderr.write("*** debug: options=%s, targets=%s\n" % (repr(options), repr(targets)))


## help
script = os.path.basename(sys.argv[0])
if options.get('h'):
    print "Usage: python %s [..options..] [..targets..]" % script
    print "  -h          :  help"
    print "  -p          :  print output"
    print "  -f file     :  datafile ('*.py' or '*.yaml')"
    print "  -n N        :  loop N times (default %d)" % ntimes
    print "  -x exclude  :  excluded target name"
    print "  -q          :  quiet mode"
    print "  -m mode     :  'class' or 'dict' (default '%s')" % mode
    print "  -k encodng  :  encoding (default None)"
    print "  -l lang     :  language ('ja') (default None)"
    sys.exit(0)


## set parameters
ntimes = int(options.get('n', ntimes))
quiet = options.get('q', quiet)
mode  = options.get('m', mode)
if mode not in ['class', 'dict']:
    sys.stderr.write("-m %s: 'dict' or 'class' expected." % mode)
    sys.exit(1)
lang = options.get('l')
encoding  = None
tostr_encoding = None   # for PyTenjin
tmpl_encoding  = None   # for PyTenjin
if options.get('e'):
    encoding       = options['e']
    tostr_encoding = None
    tmpl_encoding  = encoding
elif options.get('k'):
    encoding       = options['k']
    tostr_encoding = encoding
    tmpl_encoding  = None
    #to_str = tenjin.generate_to_str_func(tostr_encoding)
##
target_list = options.get('A') and targets_all or targets_default
if targets:
    lst = []
    for t in targets:
        if t.find('*') >= 0:
            pattern = t
            lst.extend(fnmatch.filter(target_list, pattern))
        else:
            lst.append(t)
    targets = lst
else:
    targets = target_list[:]
excludes = options.get('x')
if excludes:
    for exclude in excludes.split(','):
        if exclude in targets:
            targets.remove(exclude)
        elif exclude.find('*'):
            pattern = exclude
            for t in fnmatch.filter(targets_all, pattern):
                if t in targets:
                    targets.remove(t)
#sys.stderr.write("*** debug: ntimes=%s, targets=%s\n" % (repr(ntimes), repr(targets)))


## context data
msg("*** loading context data...\n")
datafile = options.get('f')
if not datafile:
    if mode == 'dict':
        datafile = 'bench_context.yaml'
    elif mode == 'class':
        datafile = 'bench_context.py'
    else:
        unreachable
if lang:
    datafile = re.sub(r'(\.\w+)', r'_%s\1' % lang, datafile)
context = {}
if datafile.endswith('.py'):
    exec(open(datafile).read(), globals(), context)
elif datafile.endswith('.yaml') or datafile.endswith('.yml'):
    import yaml
    s = open(datafile).read()
    if encoding:
        s = s.decode(encoding)
    context = yaml.load(s)
else:
    raise "-f %s: invalid datafile type" % datafile
#sys.stderr.write("*** debug: context=%s\n" % (repr(context)))


## generate templates
template_names = {
    'tenjin':    'bench_tenjin.pyhtml',
    'django':    'bench_django.html',
    'cheetah':   'bench_cheetah.tmpl',
    'myghty':    'bench_myghty.myt',
    'kid':       'bench_kid.kid',
    'kwartzite': 'bench_kwartzite.html',
    'kwartzite2': 'bench_kwartzite2.html',
}
msg('*** generate templates...\n')
header = open('templates/_header.html').read()
footer = open('templates/_footer.html').read()
if lang == 'ja' and encoding:
    ustr = header.decode(encoding)
    ustr = ustr.replace(u'Stock Prices', u'\u682a\u4fa1\u4e00\u89a7\u8868')
    if encoding == 'shift-jis':   charset = 'Shift_JIS'
    elif encoding == 'euc-jp':    charset = 'EUC-JP'
    else:                         charset = encoding
    ustr = ustr.replace(u'encoding="UTF-8"', u'encoding="%s"' % charset)
    ustr = ustr.replace(u'charset=UTF-8', u'charset=%s' % charset)
    header = ustr.encode(encoding)

var = None
template_names
for key, filename in template_names.iteritems():
    body = open('templates/' + filename).read()
    if mode == 'class':
        body = re.sub(r"(\w+)\['(\w+)'\]", r"\1.\2", body)
        #body = re.sub(r"(item)\['(\w+)'\]", r"\1.\2", body)
    s = header + body + footer
    if key == 'cheetah':
        if encoding:
            #s = ('#encoding %s\n' % encoding) + s
            s = ('#unicode %s\n' % encoding) + s
    elif key == 'kid':
        s = re.sub(r'<html(.*)>', r'<html\1 xmlns:py="http://purl.org/kid/ns#">', s)
    elif key == 'myghty':
        s = "<%args>\n    list\n</%args>\n" + s
        if encoding:
            s = ("# -*- coding: %s -*-\n" % encoding) + s
    open(filename, 'w').write(s)


## preparations
msg('*** preparations...\n')

if is_required('tenjin'):
    try:
        tenjin = import_module('tenjin')
        from tenjin.helpers import *
    except ImportError:
        tenjin = None

if is_required('django'):
    try:
        django = import_module('django')
        import_module('django.conf')
        django.conf.settings.configure()
        import_module('django.template')
        import_module('django.template.defaultfilters')
        #def oddeven(value):   # usage: {% forloop.counter|oddeven %}
        #    if value % 2 == 0:
        #        return "even"
        #    else:
        #        return "odd"
        #django.template.defaultfilters.register.filter(oddeven)
    except ImportError, ex:
        django = None

if is_required('cheetah'):
    template_name = template_names['cheetah']
    try:
        compiled = template_name.replace('.tmpl', '.py')
        do_with_report('compiling %s' % template_name,
                       lambda: os.system('cheetah compile %s' % template_name))
        bench_cheetah = import_module(template_name.replace('.tmpl', ''))
        bench_cheetah2 = bench_cheetah
        cheetah = True
    except ImportError:
        cheetah = None

if is_required('myghty'):
    try:
        myghty = import_module('myghty')
        myghty.interp = import_module('myghty.interp').interp
    except ImportError:
        myghty = None

if is_required('kid'):
    try:
        kid = import_module('kid')
        #kid.enable_import()
        template_name = template_names['kid']
        if not encoding:
            do_with_report('compling %s ...' % template_name,
                           lambda: kid.Template(template_name))   # compile
            #t = kid.Template(tmpl_kid)   # compile
    except ImportError:
        kid = None

if is_required('kwartzite'):
    try:
        for key in ('kwartzite', 'kwartzite2'):
            filename = template_names[key].replace('.html', '.py')
            code = open('templates/'+filename).read()
            if mode == 'class':
                code = re.sub(r"(item)\['(\w+)'\]", r"\1.\2", code)
            open(filename, 'w').write(code)
        kwartzite = import_module('kwartzite')
        kwartzite.parser = import_module('kwartzite.parser').parser
        kwartzite.parser.TextParser = import_module('kwartzite.parser.TextParser').parser.TextParser
        kwartzite.translator = import_module('kwartzite.translator').translator
        kwartzite.translator.PythonTranslator = import_module('kwartzite.translator.PythonTranslator').translator.PythonTranslator
    except Exception, ex:
        kwartzite = None
        raise


## benchmark functions

def benchmark_tenjin_convert(template_name, context, ntimes):
    if tenjin:
        remove_file(template_name + '.cache', template_name + '.marshal')
        for i in xrange(0, ntimes):
            if tostr_encoding:
                #globals()['to_str'] = tenjin.generate_to_str_func(tostr_encoding)
                context['to_str'] = tenjin.generate_to_str_func(tostr_encoding)
            template = tenjin.Template(template_name, encoding=tmpl_encoding)
        return True
    return False

def benchmark_tenjin_tmpl(template_name, context, ntimes):
    if tenjin:
        for i in xrange(0, ntimes):
            if tostr_encoding:
                #globals()['to_str'] = tenjin.generate_to_str_func(encoding)
                context['to_str'] = tenjin.generate_to_str_func(tostr_encoding)
            template = tenjin.Template(template_name, encoding=tmpl_encoding)
            output = template.render(context)
            if tmpl_encoding and isinstance(output, unicode):
                output = output.encode(tmpl_encoding)
        return output
    return False

def benchmark_tenjin(template_name, context, ntimes):
    if tenjin:
        remove_file(template_name + '.cache')
        for i in xrange(0, ntimes):
            if tostr_encoding:
                #globals()['to_str'] = tenjin.generate_to_str_func(encoding)
                context['to_str'] = tenjin.generate_to_str_func(tostr_encoding)
            engine = tenjin.Engine(cache=True, encoding=tmpl_encoding)
            output = engine.render(template_name, context)
            if tmpl_encoding and isinstance(output, unicode):
                output = output.encode(tmpl_encoding)
        return output
    return False

def benchmark_tenjin_nocache(template_name, context, ntimes):
    if tenjin:
        for i in xrange(0, ntimes):
            if tostr_encoding:
                #globals()['to_str'] = tenjin.generate_to_str_func(encoding)
                context['to_str'] = tenjin.generate_to_str_func(tostr_encoding)
            engine = tenjin.Engine(cache=False, encoding=tmpl_encoding)
            output = engine.render(template_name, context)
            if tmpl_encoding and isinstance(output, unicode):
                output = output.encode(tmpl_encoding)
        return output
    return False

def benchmark_tenjin_reuse(template_name, context, ntimes):
    if tenjin:
        remove_file(template_name + '.marshal')
        if tostr_encoding:
            #globals()['to_str'] = tenjin.generate_to_str_func(encoding)
            context['to_str'] = tenjin.generate_to_str_func(tostr_encoding)
            #context['escape'] = tenjin.html.escape_xml
        engine = tenjin.Engine(encoding=tmpl_encoding)
        for i in xrange(0, ntimes):
            output = engine.render(template_name, context)
            if tmpl_encoding and isinstance(output, unicode):
                output = output.encode(tmpl_encoding)
        #if tmpl_encoding and isinstance(output, unicode):
        #    output = output.encode(tmpl_encoding)
        return output
    return False

def benchmark_tenjin_defun(template_name, context, ntimes):
    if tenjin:
        #template = tenjin.Template(template_name, escapefunc='tenjin.escape', tostrfunc='tenjin.to_str')
        if tostr_encoding:
            #globals()['to_str'] = tenjin.generate_to_str_func(encoding)
            context['to_str'] = tenjin.generate_to_str_func(tostr_encoding)
        template = tenjin.Template(template_name, encoding=tmpl_encoding)
        sb = []; sb.append('''\
def tmpl_tenjin_view(_context):
    _buf = []
    _tmpl_tenjin_view(_buf, _context)
    return ''.join(_buf)
def _tmpl_tenjin_view(_buf, _context):
''')
        #sb.append("    locals().update(_context)\n")
        for k in context:
            sb.append("    %s = _context['%s']\n" % (k, k))
        pat = re.compile(r'^', re.M)
        sb.append(pat.sub('    ', template.script)) ; sb.append("\n")
        defun_code = ''.join(sb)
        #sys.stderr.write("*** debug: defun_code=%s\n" % (defun_code))
        exec(defun_code)
        for i in xrange(0, ntimes):
            output = tmpl_tenjin_view(context)
        return output
    return False

def benchmark_django(template_name, context, ntimes):
    if django:
        for i in xrange(0, ntimes):
            s = open(template_name).read()
            if encoding:
                s = s.decode(encoding).encode('utf-8')
            t = django.template.Template(s)
            c = django.template.Context(context)
            output = t.render(c)
            if encoding:
                output = output.decode('utf-8').encode(encoding)
        return output
    return False

def benchmark_django_reuse(template_name, context, ntimes):
    if django:
        s = open(template_name).read()
        if encoding:
            s = s.decode(encoding).encode('utf-8')
        t = django.template.Template(s)
        c = django.template.Context(context)
        for i in xrange(0, ntimes):
            output = t.render(c)
            if encoding:
                output = output.decode('utf-8').encode(encoding)
        return output
    return False

def benchmark_cheetah(template_name, context, ntimes):
    if cheetah:
        for i in xrange(0, ntimes):
            template = bench_cheetah.bench_cheetah()
            for key, val in context.iteritems():
                setattr(template, key, val)
            output = template.respond()
            if encoding:
                output = output.encode(encoding)
        return output
    return False

def benchmark_cheetah_reuse(template_name, context, ntimes):
    if cheetah:
        template = bench_cheetah.bench_cheetah()
        for key, val in context.iteritems():
            setattr(template, key, val)
        for i in xrange(0, ntimes):
            output = template.respond()
            if encoding:
                output = output.encode(encoding)
        #for key in context.keys():
        #    delattr(template, key)
        return output
    return False

def benchmark_myghty(template_name, context, ntimes):
    if myghty:
        _encoding = encoding or sys.getdefaultencoding()
        for i in xrange(0, ntimes):
            interpreter = myghty.interp.Interpreter(component_root='.', output_encoding=_encoding)
            component = interpreter.make_component(open(template_name).read())
            buf = StringIO()
            interpreter.execute(component, request_args=context, out_buffer=buf)
            output = buf.getvalue()
            buf.close()
        return output
    return False

def benchmark_myghty_reuse(template_name, context, ntimes):
    if myghty:
        _encoding = encoding or sys.getdefaultencoding()
        interpreter = myghty.interp.Interpreter(component_root='.', output_encoding=_encoding)
        component = interpreter.make_component(open(template_name).read())
        for i in xrange(0, ntimes):
            buf = StringIO()
            interpreter.execute(component, request_args=context, out_buffer=buf)
            output = buf.getvalue()
            buf.close()
        return output
    return False

def benchmark_kid(template_name, context, ntimes):
    if kid:
        for i in xrange(0, ntimes):
            if encoding:
                s = open(template_name).read().decode(encoding).encode('utf-8')
                template = kid.Template(source=s, encoding=encoding)
            else:
                template = kid.Template(file=template_name)
            for key, val in context.iteritems():
                setattr(template, key, val)
            output = template.serialize(encoding=encoding)
            for key in context.keys():
                delattr(template, key)
        return output
    return False

def benchmark_kid_reuse(template_name, context, ntimes):
    if kid:
        template = kid.Template(file=template_name)
        for key, val in context.iteritems():
            setattr(template, key, val)
        for i in xrange(0, ntimes):
            output = template.serialize()
        for key in context.keys():
            delattr(template, key)
        return output
    return False


def _compile_kwartzite_template(template_name, encoding=None):
    parser = kwartzite.parser.TextParser.TextParser()
    parsed_data = parser.parse_file(template_name)
    translator = kwartzite.translator.PythonTranslator.PythonTranslator()
    code = translator.translate(parsed_data, encoding=encoding)
    return code

def benchmark_kwartzite(template_name, context, ntimes):
    if not kwartzite:
        return False
    filename = template_name.replace('.html', '_html.py')
    #remove_file(filename)
    #remove_file(filename+'c')
    code = _compile_kwartzite_template(template_name)
    open(filename, 'w').write(code)
    for i in xrange(0, ntimes):
        import bench_kwartzite
        template = bench_kwartzite.bench_kwartzite(**context)
        output = template.create_document()
    return output

def benchmark_kwartzite_nocache(template_name, context, ntimes):
    if not kwartzite:
        return False
    filename = template_name.replace('.html', '_html.py')
    #remove_file(filename)
    #remove_file(filename+'c')
    for i in xrange(0, ntimes):
        code = _compile_kwartzite_template(template_name)
        open(filename, 'w').write(code)
        import bench_kwartzite
        template = bench_kwartzite.bench_kwartzite(**context)
        output = template.create_document()
    return output

def benchmark_kwartzite2(template_name, context, ntimes):
    if not kwartzite:
        return False
    filename = template_name.replace('.html', '_html.py')
    #remove_file(filename)
    #remove_file(filename+'c')
    code = _compile_kwartzite_template(template_name)
    open(filename, 'w').write(code)
    for i in xrange(0, ntimes):
        import bench_kwartzite2
        template = bench_kwartzite2.bench_kwartzite2(**context)
        output = template.create_document()
    return output

def benchmark_kwartzite2_nocache(template_name, context, ntimes):
    if not kwartzite:
        return False
    filename = template_name.replace('.html', '_html.py')
    #remove_file(filename)
    #remove_file(filename+'c')
    for i in xrange(0, ntimes):
        code = _compile_kwartzite_template(template_name)
        open(filename, 'w').write(code)
        import bench_kwartzite2
        template = bench_kwartzite2.bench_kwartzite2(**context)
        output = template.create_document()
    return output


## benchmark function table
names = globals().keys()
func_table = {}
for name in names:
    if name.startswith('benchmark_'):
        func = globals()[name]
        if callable(func):
            name = name[len('benchmark_'):]
            func_table[name] = func
            func_table[re.sub(r'_', '-', name)] = func


## benchmark
msg('*** start benchmark\n')

print  "*** ntimes=%d" % ntimes
#print "             target        utime      stime      total       real"
print  "                           utime      stime      total       real"

for target in targets:
    print "%-20s " % target,
    sys.stdout.flush()

    ## start time
    start_t = time.time()
    t1 = os.times()

    ## call benchmark function
    func = func_table[target]
    key  = re.split(r'[-_]', target)[0]
    done = False
    if func:
        output = func.__call__(template_names[key], context, ntimes)
        done = output and True or False
    else:
        sys.stderr.write("*** %s: invalid target.\n" % target)
        sys.exit(1)

    ## end time
    t2 = os.times()
    end_t = time.time()

    ## result
    if done:
        utime = t2[0]-t1[0]
        stime = t2[1]-t1[1]
        #total = t2[4]-t1[4]
        total = utime + stime
        real  = end_t-start_t
        #print "%-20s  %10.5f %10.5f %10.5f %10.5f" % (target, utime, stime, total, real)
        print         "%10.5f %10.5f %10.5f %10.5f" % (        utime, stime, total, real)
    else:
        #print "%-20s     (module not installed)" % target
        print         "   (module not installed)"

    ## print output
    if options.get('p'):
        if isinstance(output, str):
            fname = '%s.result' % target
            open(fname, 'w').write(output)
            msg('*** output created: %s\n' % fname)


