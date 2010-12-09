###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'oktest'

require 'kwartzite/parser/text'


module Kwartzite


  class TextScanner::TestCase
    include Oktest::TestCase

    def test_scan_tag
      input1 = <<END
<div id="outer">
  <div data-kwd="mark:x" id="y"
       class="z">
    <p><foo/><input type="text"><br></p>
    <input type="text" data-kwd="mark:x2">
    <div id="inner">xxx</div>
  </div>
</div>
END
      scanner = TextScanner.new(input1)
      t = nil
      spec "scans tags." do
        t = scanner.scan_tag(nil)
        ok {t}.is_a?(Tag)
        ok {t.name} == 'div'
        ok {t.kind} == :stag
      end
      spec "gets attributes." do
        # falldown
        ok {t.attrs} == [[" ", "id", "y"], ["\n       ", "class", "z"]]
      end
      spec "gets directive string." do
        # falldown
        ok {t.directive} == "mark:x"
      end
      spec "text before tag is kept in @text." do
        # falldown
        ok {scanner.text} == %Q`<div id="outer">\n`
      end
      spec "skips end tag if tag name is not equal to nested tag name."
      spec "skips empty tag if it doesn't have directive."
      spec "skips start tag if no directives."
      spec "skips start tag if not nested tag name." do
        # falldown
        t = scanner.scan_tag('div')
        ok {scanner.text} == %Q`    <p><foo/><input type="text"><br></p>\n`
      end
      spec "regards '<input>', '<br>', ... as empty tag forcedly." do
        # falldown
        ok {t.name} == 'input'
        ok {t.kind} == :empty
        ok {t.directive} == 'mark:x2'
      end
      spec "clears empty_slash of tag object if empty_slash is not specified." do
        # falldown
        ok {t.empty_slash} == nil
      end
      spec "if tag found then returns it." do
        # falldown
        t = scanner.scan_tag('div')
        ok {t}.is_a?(Tag)
        ok {t.name} == 'div'
        ok {t.kind} == :stag
        ok {t.attrs} == [[" ", "id", "inner"]]
        ok {t.directive} == nil
        #
        t = scanner.scan_tag('div')
        ok {t.name} == 'div'
        ok {t.kind} == :etag
        #
        t = scanner.scan_tag('div')
        ok {t.name} == 'div'
        ok {t.kind} == :etag
      end
      spec "returns nil if reached to end of input string." do
        # falldown
        t = scanner.scan_tag(nil)
        ok {t} == nil
      end
      spec "rest text is kept in @text." do
        # falldown
        ok {scanner.text} == "</div>\n"
      end
    end

    def test_empty_tag_name?
      spec "returns true if tag_name is one of 'input', 'img', 'br', 'hr', 'meta', and 'link'." do
        scanner = TextScanner.new(nil)
        ['input', 'img', 'br', 'hr', 'meta', 'link'].each do |tag_name|
          ok {scanner.__send__(:empty_tag_name?, tag_name)} == true
        end
        ['div', 'span'].each do |tag_name|
          ok {scanner.__send__(:empty_tag_name?, tag_name)} == false
        end
      end
    end

  end


  class TextParser::TestCase
    include Oktest::TestCase

    def test_parse
      input = <<END
<div id="outer">
  <div id="middle" data-kwd="mark:main">
    <div id="inner">
      <label>Text</label>
      <input type="text" data-kwd="mark:text">
    </div>
  </div>
</div>
END
      spec "returns nodes." do
        parser = TextParser.new
        ret = parser.parse(input, 'example.html')
        ok {ret[0]} == %Q`<div id="outer">\n`
        ok {ret[1]}.is_a?(Element)
        ok {ret[1].stag.directive} == 'mark:main'
        ok {ret[1].children[0]} == "    <div id=\"inner\">\n      <label>Text</label>\n"
        ok {ret[1].children[1]}.is_a?(Element)
        ok {ret[1].children[1].stag.directive} == 'mark:text'
        ok {ret[1].children[2]} == "    </div>\n"
        ok {ret[1].children.length} == 3
        ok {ret[2]} == "</div>\n"
      end
      spec "raises ParseError if start-tag is not closed by corresponding end-tag." do
        input2 = <<END
<ul data-kwd="mark:items">
  <li data-kwd="mark:item">foo
</ul>
END
        parser = TextParser.new
        pr = proc { parser.parse(input2, 'ex2.html') }
        ok {pr}.raise?(ParseError, "tag '<li>' is not closed.")
      end
    end

  end


end
