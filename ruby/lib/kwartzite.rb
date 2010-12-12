###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module Kwartzite

  VERSION = "$Release: 0.0.0 $".split(' ')[1]

end

require 'kwartzite/parser'
require 'kwartzite/parser/text'
require 'kwartzite/translator'
require 'kwartzite/translator/ruby'
require 'kwartzite/director'
require 'kwartzite/safe_str'
require 'kwartzite/template'
require 'kwartzite/html'
require 'kwartzite/util'
