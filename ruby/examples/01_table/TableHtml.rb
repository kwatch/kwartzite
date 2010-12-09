require './TableHtml_.rb'

class TableHtml < TableHtml_

  def initialize(items)
    @items = items
  end

  def elem_items()
    @i = 0
    for @item in @items
      @i += 1
      klass = @i % 2 == 1 ? 'odd' : 'even'
      super(:class=>klass)
      ### or
      #stag_items(:class=>klass)   # start tag
      #cont_items()                # content
      #etag_items()                # end tag
    end
  end

  def cont_item()
    echo @item
  end
  ### or
  #def elem_item()
  #  stag_item()
  #  echo @item
  #  etag_item()
  #end

end
