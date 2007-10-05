# -*- coding: utf-8 -*-
###
### $Rev$
### $Release$
### $Copyright$
###

import unittest
from test import test_support
import sys, os, re, traceback
from glob import glob
from cStringIO import StringIO

from testcase_helper import *
from kwartzite.main import Main


CURR_DIR   = os.getcwd()
SANDBOX    = '_sandbox'
DATA_DIR   = CURR_DIR + '/testdata/test_main'
INPUT_HTML = open(DATA_DIR + '/input.html').read()
EXPECTED_TEXT_PYTHON = open(DATA_DIR + '/test_text_python.expected').read()
EXPECTED_TEXT_JAVA   = open(DATA_DIR + '/test_text_java.expected').read()
EXPECTED_XML_PYTHON  = open(DATA_DIR + '/test_xml_python.expected').read()
EXPECTED_XML_JAVA    = open(DATA_DIR + '/test_xml_java.expected').read()

PYTHON_TRANSLATOR_PROPERTIES = '--classname=%F --baseclass=TemplateObject --encoding=UTF8 --mainprog=false --context=no --nullobj=true --fragment=yes --attrobj=False'
JAVA_TRANSLATOR_PROPERTIES = '--classname=%F --baseclass=TemplateObject --interface=kwartzite.Template --encoding=UTF8 --mainprog=false --context=no --nullobj=true --fragment=yes'



class MainTest(unittest.TestCase, TestCaseHelper):


    debug     = False
    options   = ()
    filename  = None
    classname = None
    input     = None
    expected  = None
    outfile   = None
    exception = None
    errormsg  = None


    def setUp(self):
        try:
            dirname = SANDBOX
            if not os.path.exists(dirname):
                os.mkdir(dirname)
            os.chdir(dirname)
        except Exception, ex:
            print >>sys.stderr, str(ex)
            sys.exit(1)


    def tearDown(self):
        if os.environ.get('TEST'): return
        try:
            for fname in glob('*') + glob('.*'):
                os.unlink(fname)
            os.chdir(CURR_DIR)
            os.rmdir(SANDBOX)
            #os.chdir(CURR_DIR)
            #os.removedirs(SANDBOX)
        except Exception, ex:
            print >>sys.stderr, str(ex)
            sys.exit(1)


    def _test(self):
        #funcname = sys._getframe().f_code.co_name
        #funcname = sys._getframe().f_back.f_code.co_name
        try:
            funcname = self._TestCase__testMethodName
        except AttributeError:
            funcname = self._testMethodName
        testname = funcname[len('test_'):]
        #filenames = []
        try:
            #
            input = self.input
            assert input is not None
            #
            filename = self.filename
            if filename is None:
                filename = funcname.replace('_', '-') + '.html'
            if filename:
                open(filename, 'w').write(input)
            #
            argv = ['pysio2']
            options = self.options
            if isinstance(options, str):
                options = options.split(' ')
            if options:
                argv.extend(options)
            if filename:
                argv.append(filename)
            #
            classname = self.classname
            if classname is None:
                basename = os.path.splitext(filename)[0]
                classname = re.sub('[^\w]', '_', basename) + '_html'
            #
            expected = self.expected
            if expected is True:
                expected = open("%s/%s.expected" % (DATA_DIR, funcname)).read()
            if expected is not None:
                if filename:
                    expected = expected.replace('FILENAME', filename)
                if classname:
                    expected = expected.replace('CLASSNAME', classname)
            #
            if self.debug:
                sys.stderr.write("*** %s.%s(): argv=%s\n" % (self.__class__.__name__, funcname, repr(argv)))
            stdout = StringIO()
            stderr = StringIO()
            if self.exception:
                arr = [None]
                def f():
                    try:
                        Main(argv, stdout=stdout, stderr=stderr).execute()
                    except Exception, ex:
                        arr[0] = ex
                        raise
                self.assertRaises(self.exception, f)
                if self.errormsg:
                    ex = ar[0]
                    self.assertEquals(self.errormsg, str(ex))
            else:
                Main(argv, stdout=stdout, stderr=stderr).execute()
                if self.outfile:
                    outfile = self.outfile
                    self.assertTrue(os.path.isfile(outfile),
                                    "file '%s' expected but not generated." % outfile)
                    if self.expected:
                        actual = open(outfile).read()
                        self.assertTextEqual(expected, actual)
                else:
                    actual = stdout.getvalue()
                    self.assertTextEqual(expected, actual)
        finally:
            #for fname in filenames:
            #    if os.path.exists(fname):
            #        os.remove(fname)
            pass


    def _shell_command(infile=None, outfile=None, options=None):
        vars = {
            'datadir':'testdata/test_main',
            'infile':infile,
            'outfile':outfile,
            'options':options,
        }
        buf = []
        append = buf.append
        append(    'cp %(datadir)s/input.html %(infile)s\n')
        append(    'pysio2 %(options)s -o %(outfile)s %(infile)s\n')
        if options.find('--classname=') < 0:
            append("perl -pi -e 's/%(infile)s/FILENAME/g; s/%(class)s/CLASSNAME/g' %(outfile)s\n")
            vars['class'] = re.sub(r'[^\w]', '_', infile)
        append(    'mv %(outfile)s %(datadir)s\n')
        append(    'rm %(infile)s\n')
        return ''.join(buf) % vars



    def test_text_python(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        self.expected  = EXPECTED_TEXT_PYTHON  # or True
        self._test()

    shell_command_to_generate_test_text_python_expected = \
        _shell_command('test-text-python.html', 'test_text_python.expected', '')


    def test_text_java(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        self.expected  = EXPECTED_TEXT_JAVA  # or True
        self.options   = "-t java"
        self._test()

    shell_command_to_generate_test_text_java_expected = \
        _shell_command('test-text-java.html', 'test_text_java.expected', '-t java')


    def test_xml_python(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        self.expected  = EXPECTED_XML_PYTHON  # or True
        self.options   = "-p xml"
        self._test()

    shell_command_to_generate_test_xml_python_expected = \
        _shell_command('test-xml-python.html', 'test_xml_python.expected', '-p xml')


    def test_xml_java(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        self.expected  = EXPECTED_XML_JAVA  # or True
        self.options   = "-pxml -tjava"
        self._test()

    shell_command_to_generate_test_xml_java_expected = \
        _shell_command('test-xml-java.html', 'test_xml_java.expected', '-pxml -tjava')


    def test_out_file_1(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        #self.expected  = EXPECTED_TEXT_PYTHON
        self.options   = "-o (%c)(%u)(%b)(%x)(%%x).py"
        self.outfile   = "(test_out_file_1_html)(test_out_file_1)(test-out-file-1)(html)(%x).py"
        self._test()


    def test_out_file_2(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        #self.expected  = EXPECTED_TEXT_PYTHON
        self.options   = "-o (%C)(%U)(%B)(%X)(%%X).py"
        self.outfile   = "(TestOutFile2Html)(TestOutFile2)(TestOutFile2)(Html)(%X).py"
        self._test()


    def test_out_file_3(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        #self.expected  = EXPECTED_TEXT_PYTHON
        #self.classname = TestOutFile3Page
        self.options   = "-o %c.py --classname=%BPage"
        self.outfile   = "TestOutFile3Page.py"
        self._test()


    def test_python_classname(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        self.expected  = EXPECTED_TEXT_PYTHON
        self.classname = 'TestPythonClassnameHtml'
        self.options   = "--classname=%B%X"
        self._test()


    def test_java_classname(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        self.expected  = EXPECTED_TEXT_JAVA
        self.classname = 'TestJavaClassnameHtml'
        self.options   = "-t java --classname=%B%X"
        self._test()


    def test_python_properties(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        self.expected  = True
        self.options   = '-tpython '+PYTHON_TRANSLATOR_PROPERTIES
        self._test()

    shell_command_to_generate_test_python_properties_expected_file = \
        _shell_command('test-python-properties.html',
                       'test_python_properties.expected',
                       '-tpython '+PYTHON_TRANSLATOR_PROPERTIES)


    def test_java_properties(self):
        #self.debug     = True
        self.input     = INPUT_HTML
        self.expected  = True
        self.options   = '-tjava '+JAVA_TRANSLATOR_PROPERTIES
        self._test()

    shell_command_to_generate_test_java_properties_expected_file = \
        _shell_command('test-java-properties.html',
                       'test_java_properties.expected',
                       '-tjava '+JAVA_TRANSLATOR_PROPERTIES)



name = os.environ.get('TEST')
if name:
    for m in dir(MainTest):
        if m.startswith('test_') and m != 'test_'+name:
            delattr(MainTest, m)


def test_main():
    test_support.run_unittest(MainTest)


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'COMMAND':
        for s in dir(MainTest):
            if s.startswith('shell_command'):
                print getattr(MainTest, s)
    else:
        test_main()
