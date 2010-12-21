###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

$: << '.' unless $:.include?('.')
dirpath = __FILE__.sub(/_test\.rb$/, '')
#Dir.glob("#{dirpath}/**/*_test.rb").each {|test_file| require test_file }
test_files = [
  "util_test.rb",
  "parser_test.rb",
  "parser/text_test.rb",
  "translator_test.rb",
  "translator/ruby_test.rb",
  "translator/python_test.rb",
  "director_test.rb",
  "template_test.rb",
  "html_test.rb",
  "main_test.rb",
].collect {|fpath| File.join(dirpath, fpath) }
diff = Dir.glob("#{dirpath}/**/*_test.rb") - test_files
raise "NOT TESTED: #{diff.join(', ')}" unless diff.empty?
test_files.each {|test_file| require test_file }
