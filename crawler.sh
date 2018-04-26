scrapy runspider src/main/hesperian/wiki_crawler/crawler.py -o src/main/hesperian/wiki_crawler/wiki_words.csv -s LOG_LEVEL=INFO
python3 src/main/hesperian/wiki_crawler/clean_tokens.py src/main/hesperian/wiki_crawler/wiki_words.csv src/main/hesperian/wiki_crawler/wiki_word_counts.txt
