import sys, os
from bench_kwartzite2_html import *

class bench_kwartzite2(bench_kwartzite2_html):

  if os.environ.get('FAST'):
    sys.stderr.write('*** debug: fast mode')

    def elem_stocks(self):
        n = 0
        for item in self.list:
            n += 1
            self.attr_stocks['class'] = n % 2 and 'odd' or 'even'
            self.text_n           = n
            self.text_symbol      = item['symbol']
            self.attr_symbol['href'] = '/stocks/'+item['symbol']
            self.text_url         = item['url']
            self.attr_url['href'] = item['url']
            self.text_price       = item['price']
            self.text_change      = item['change']
            self.text_ratio       = item['ratio']
            if item['change'] < 0.0:
                self.attr_change['class'] = 'minus'
                self.attr_ratio['class']  = 'minus'
            else:
                self.attr_change.pop('class', None)
                self.attr_ratio.pop('class', None)
            #
            self.stag_stocks()
            self.cont_stocks()
            self.etag_stocks()

  else:

    def elem_stocks(self):
        n = 0
        for item in self.list:
            n += 1
            self.put_stocks('class', n % 2 and 'odd' or 'even')
            self.set_n(n)
            self.set_symbol(item.symbol)
            self.put_symbol('href', '/stocks/'+item.symbol)
            self.set_url(item.url)
            self.put_url('href', item.url)
            self.set_price(item.price)
            self.set_change(item.change)
            self.set_ratio(item.ratio)
            if item.change < 0.0:
                self.put_change('class', 'minus')
                self.put_ratio('class', 'minus')
            else:
                self.put_change('class', None)
                self.put_ratio('class', None)
            #
            self.stag_stocks()
            self.cont_stocks()
            self.etag_stocks()
