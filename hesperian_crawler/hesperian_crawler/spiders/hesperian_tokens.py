# -*- coding: utf-8 -*-
import scrapy


class HesperianTokensSpider(scrapy.Spider):
    name = 'hesperian_tokens'
    # allowed_domains = ['http://en.hesperian.org/']
    start_urls = ['http://en.hesperian.org/hhg/Healthwiki']



    def parse(self, response):
    	for title in response.css('div#bodyContent td span a::attr(href)').extract():
    		yield response.follow(title, callback=self.parse_table_of_contents)

        
    def parse_table_of_contents(self, response):
    	# Get text
    	# words = response.css('div.toc ul li a::text').re(r'\w+')
    	# for token in words:
    	# 	yield {'token': token.lower()}

    	start = response.css('div.toc a::attr(href)').extract_first()
    	if start is not None:
    		yield response.follow(start, callback=self.parse_wiki)


    def parse_wiki(self, response):
    	words = response.css("div#bodyContent ::text").re(r'\w+')
    	for token in words:
    		yield {'token' : token.lower()}

    	next_page = response.xpath("//a[contains(., 'NEXT →')]/@href").extract_first()
    	if next_page is not None:
    		yield response.follow(next_page, callback=self.parse_wiki)
