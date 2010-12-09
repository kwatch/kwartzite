###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'

require 'kwartzite/html'


module Kwartzite


  class Html::TestCase
    include Oktest::TestCase
    include Html

    def test_escape
      spec "escapes html special characters unless value is a SafeStr." do
        ok {escape('abc<>&"')} == 'abc&lt;&gt;&amp;&quot;'
        ok {escape(SafeStr.new('abc<>&"'))} == 'abc<>&"'
      end
    end

    def test_escape_html
      ret = escape_html('<>&"')
      spec "escapes html special characters" do
        ok {ret} == '&lt;&gt;&amp;&quot;'
      end
      spec "returns SafeStr object." do
        ok {ret}.is_a?(SafeStr)
      end
    end

    def test_escape_html2
      ret = escape_html2('<>&"')
      spec "escapes html special characters" do
        ok {ret} == '&lt;&gt;&amp;&quot;'
      end
      spec "returns SafeStr object." do
        ok {ret}.is_a?(SafeStr)
      end
    end

    def test_new_cycle
      ret = new_cycle('<AAA>', 'B&B', SafeStr.new('<C&C>'))
      spec "returns new Cycle object." do
        ok {ret}.is_a?(Util::Cycle)
      end
      spec "escapes all values." do
        ok {ret.to_s} == '&lt;AAA&gt;'
        ok {ret.to_s} == 'B&amp;B'
        ok {ret.to_s} == '<C&C>'
        ok {ret.to_s} == '&lt;AAA&gt;'
      end
    end

    def test_checked
      spec "returns 'checked' if true value." do
        ok {checked(1==1)} == 'checked'
      end
      spec "returns nil if false value." do
        ok {checked(1==0)} == nil
      end
    end

    def test_selected
      spec "returns 'selected' if true value." do
        ok {selected(1==1)} == 'selected'
      end
      spec "returns nil if false value." do
        ok {selected(1==0)} == nil
      end
    end

    def test_disabled
      spec "returns 'disabled' if true value." do
        ok {disabled(1==1)} == 'disabled'
      end
      spec "returns nil if false value." do
        ok {disabled(1==0)} == nil
      end
    end

  end


  class HtmlTemplate::TestCase
    include Oktest::TestCase

    def test___class__
      spec "HtmlTemplate includes Html module." do
        ok {HtmlTemplate.ancestors}.include?(Html)
      end
    end

  end


end
