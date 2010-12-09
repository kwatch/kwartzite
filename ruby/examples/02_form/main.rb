###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

module View
end

require './view/FormHtml.rb'

def main
  params = {
    'user.gender'         => 'M',
    'user.favorite'       => 'sasaki',
    'user.goods.tvseries' => 'y',
  }
  html = View::FormHtml.new(params)
  print html.render()
end

if __FILE__ == $0
  main()
end
