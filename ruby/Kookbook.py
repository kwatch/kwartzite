###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

kook_default_product = 'test'

@recipe
def test(c):
    """do test"""
    system("ruby test/kwartzite_test.rb")

