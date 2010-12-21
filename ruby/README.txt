= README

$Release: $



== About Kwartzite

Kwartzite is a simple template engine especially for web application.
Kwartzite uses Generation Gap Pattern to separate presentation logics
from HTML template files.



== Features

* Designer-friendly template (pure HTML)
* Separated presentation logics
* Very simple mechanism (generation-gap pattern)
* Not fastest, but enough fast



== Example

example.html:

    <table>
      <tr class="odd" data-kwd="mark:items">
        <td data-kwd="value:item">foo</td>
      </tr>
      <tr class="even" data-kwd="dummy:">
        <td>bar</td>
      </tr>
    </table>


Command-line:

    $ bin/rbkwartzite example.html > ExampleHtml_.rb
    ### or
    $ bin/rbkwartzite -c '%C_' -o '%C_.rb' *.html


ExampleHtml.rb:

    require './ExampleHtml_.rb'
    
    class ExampleHtml < ExampleHtml_
    
      def initialize(items)
        @items = items
      end
    
      def elem_items
        is_odd = false
        for @item in @items
          is_odd = ! is_odd
          klass = is_odd ? 'odd' : 'even'
          super(:class=>klass)
          ### or
          #stag_items(:class=>klass)   # start tag
          #cont_items()                # content
          #etag_items()                # end tag
        end
      end
    
    end
    

main.rb:

    require './ExampleHtml.rb'
    items = ['Haruhi', 'Mikuru', 'Yuki']
    html = ExampleHtml.new(items)
    print html.render()


Output:

    <table>
      <tr class="odd">
        <td>Haruhi</td>
      </tr>
      <tr class="even">
        <td>Mikuru</td>
      </tr>
      <tr class="odd">
        <td>Yuki</td>
      </tr>
    </table>



== Auto Escaping

Kwartzite escapes html special characters (<>&") automatically.
If you don't want to escape a certain expression, use safe_str() helper.

In the below example, '<b>Kyon</b>' is escaped automatically but
'<b>Itsuki</b>' is not, because safe_str() is called for the latter.


main2.rb:

    require './ExampleHtml.rb'
    items = ['<b>Kyon</b>', safe_str('<b>Itsuki</b>')]
    html = ExampleHtml.new(items)
    print html.render()


Output:

    <table>
      <tr class="odd">
        <td>&lt;b&gt;Kyon&lt;/b&gt;</td>
      </tr>
      <tr class="even">
        <td><b>Itsuki</b></td>
      </tr>
    </table>



== Helper Methods


: safe_str(value)

	Returns SafeStr object which is a string that is regarded as safe.
	NOTICE: this helper doesn't escape HTML special characters!

	    safe_str('<b>SOS</b>')       #=> SafeStr object


: escape(value)

	Escapes HTML special characters in values.
	If value is an instance of SafeStr, do nothing.

	    escape('<b>SOS</b>')            #=> "&lt;b&gt;SOS&lt;/b&gt;"
	    escape(safe_str('<b>SOS</b>'))  #=> "<b>SOS</b>"


: new_cycle(val1, val2, ...)

	Returns new Cycle object. Argument values should be escaped in advance.

	    cycle = new_cycle('odd', 'even')
	    cycle.to_s   #=> "odd"
	    cycle.to_s   #=> "even"
	    cycle.to_s   #=> "odd"
	    cycle.to_s   #=> "even"


: checked(value)

	Returns "checked" string if value is not nil nor false,
	else returns nil.

	    checked(1==1)   #=> "checked"
	    checked(1==0)   #=> nil

	This is intended to use with <input> tag.

	    <input type="checkbox" name="confirmed" value="y"
	           data-kwd="mark:confirmed">Yes, I confirmed.

	    def elem_confirmed
	      super(:checked=>checked(@params['confirmed']=='y'))
	    end


: selected(value)

	Returns "selected" string if value is not nil nor false,
	else returns nil.
                   
	    selected(1==1)   #=> "selected"
	    selected(1==0)   #=> nil

	This is intended to use with <option> tag.

	    <option value="" data-kwd="mark:favorite">name</a>

	    def elem_favorite
	      curr = @params['favorite']
	      [ ['h', 'Haruhi'],
	        ['m', 'Mikuru'],
	        ['y', 'Yuki'],
              ].each do |k, v|
	        stag_favorite(:value=>k, :selected=>select(curr == k))
		echo v
	        etag_favorite
	      end
	    end


: disabled(value)

	Returns "disabled" string if value is not nil nor false,
	else returns nil.
                   
	    disabled(1==1)   #=> "disabled"
	    disabled(1==0)   #=> nil



== Directives

'Directive' means special command for temlate. Kwartzite directive is
described in 'data-kwd' attributes.


: data-kwd="mark:xxx"

	Defines 'elem_xxx()', 'stag_xxx()', 'cont_xxx()', and 'etag_xxx()'
	methods.

: data-kwd="value:expr"

	Replaces content of the element with 'expr'.
	This is almost same as 'def cont_xxx; echo @expr; end'.
	For example:

	    <li data-kwd="value:item">foo</li>

	is almost same as:

	    <li data-kwd="mark:item">foo</li>

	    def cont_item
	      echo @item
	    end

	Notice that 'expr' should be common-expression (see below section).

: data-kwd="dummy:"

	Removes the element. This is almost same as:

	   <li data-kwd="value:dummy">foo</li>

	   def elem_dummy
	     # pass
	   end



== Common Expression

Kwartzite supports multi progamming languages, therefore embedded expression
should be common with these languages.

Kwartzite converts common expression into target programming language code.


: var_name
	* Ruby: @var_name
	* Python: self.var_name
	* Java: _varName

: var.attr_name
	* Ruby: @var.attr_name
	* Python: self.var.attr_name
	* Java: _var.getAttrName()

: var['key_name']
	* Ruby: @var['key_name']
	* Python: self.var['key_name']
	* Java: _var.get("key_name")



== Copyright and License

$Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $

$License: MIT License $
