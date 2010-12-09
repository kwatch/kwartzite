###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require './TableHtml.rb'

def main()
  items = ['Haruhi', 'Mikuru', 'Yuki']
  html = TableHtml.new(items)
  print html.render()
end

def main2()
  require 'kwartzite'
  include SafeStr::Helper
  items = ['<b>Haruhi</b>', '<b>Mikuru</b>', safe_str('<b>Yuki</b>')]
  html = TableHtml.new(items)
  print html.render()
end


if __FILE__ == $0
  flag_escape = ARGV[0] == '-e'
  if ! flag_escape
    main()
  else
    main2()
  end
end
