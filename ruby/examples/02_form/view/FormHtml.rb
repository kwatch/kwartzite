###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require './view/FormHtml_.rb'

class View::FormHtml < View::FormHtml_

  CHARACTERS = [
    ['haruhi',    'Haruhi Suzumiya'],
    ['mikuru',    'Mikuru Asahina'],
    ['yuki',      'Yuki Nagato'],
    #['itsuki',    'Itsuki Koizumi'],
    #['kyon',      'Kyon'],
    ['tsuruya',   'Tsuruya-san'],
    #['taniguchi', 'Taniguchi'],
    #['kunikida',  'Kunikida'],
    #['sister',    'Kyon\'s sister'],
    #['sonoo',     'Snoo Mori'],
    ['sasaki',    'Sasaki'],
    #['kyoko',     'Kyoko Tachibana'],
    #['kuyou',     'Kuyou Suhou'],
  ]

  def initialize(params)
    @params = params
  end

  def elem_DOCUMENT()
    elem_user_form()
  end

  def elem_user_form
    super(:action=>'/sos/user-form.cgi')
  end

  def elem_user_name
    super(:value=>@params['user.name'])
  end

  def elem_user_password
    super(:value=>@params['user.password'])
  end

  def elem_user_gender_M
    super(:checked=>checked(@params['user.gender'] == 'M'))
    ### or
    #val = @params['user.gender'] == 'M' ? 'checked' : nil
    #super(:checked=>val)
  end

  def elem_user_gender_W
    super(:checked=>checked(@params['user.gender'] == 'W'))
    ### or
    #val = @params['user.gender'] == 'W' ? 'checked' : nil
    #super(:checked=>val)
  end

  def elem_user_favorite
    curr_value = @params['user.favorite']
    CHARACTERS.each do |value, label|
      stag_user_favorite(:value=>value, :selected=>selected(curr_value == value))
      ### or
      #selected = curr_value == value ? 'selected' : nil
      #stag_user_favorite(:value=>value, :selected=>selected)
      echo label   # instead of cont_user_favorite()
      etag_user_favorite()
    end
  end

  def elem_user_goods_novels
    super(:checked=>checked(@params['user.goods.novels'] == 'y'))
    ### or
    #val = @params['user.goods.novels'] == 'y' ? 'checked' : nil
    #super(:checked=>val)
  end

  def elem_user_goods_tvseries
    super(:checked=>checked(@params['user.goods.tvseries'] == 'y'))
  end

  def elem_user_goods_movie
    super(:checked=>checked(@params['user.goods.movie'] == 'y'))
  end

end
