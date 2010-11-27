###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


class SafeStr < String

  module Helper

    def safe_str(value)
      return SafeStr.new(value)
    end

  end

end unless defined?(SafeStr)
