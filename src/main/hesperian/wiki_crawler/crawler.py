import scrapy

class HesperianTokensSpider(scrapy.Spider):
    name = 'hesperian_tokens'
    start_urls = ['http://en.hesperian.org/hhg/Special:AllPages']
    allowed_domains = ['en.hesperian.org']

    def parse(self, response):
      all_pages_url = "http://en.hesperian.org/hhg/Special:AllPages?from=&to=&namespace="
      for value in response.css('select.namespaceselector option::attr(value)').extract():
        yield response.follow("{}{}".format(all_pages_url, value), callback=self.parse_allPages)

      yield response.follow("http://en.hesperian.org/hhg/HealthWiki", callback=self.parse_main)

    def parse_allPages(self, response):
      for page in response.css('ul.mw-allpages-chunk li a::attr(href)').extract():
        yield response.follow(page, callback=self.parse_page)

    def parse_page(self, response):
      words = set(response.css("div#bodyContent ::text").re(r'\w+'))
      for token in words:
        yield {'token' : token.lower()}

    def parse_main(self, response):
      for book in response.css('div#bodyContent td span a::attr(href)').extract():
        yield response.follow(book, callback=self.parse_table_of_contents)

    def parse_table_of_contents(self, response):
      for page in response.css('div.toc a::attr(href)').extract():
        yield response.follow(page, callback=self.parse_page)

      yield parse_page(response)
