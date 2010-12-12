###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


unless defined?(SafeStr)

  class SafeStr < String
  end

  def safe_str(value)
    return SafeStr.new(value)
  end

end
