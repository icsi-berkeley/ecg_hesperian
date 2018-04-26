import sys
import time
from pprint import pprint
from nluas.language.analyzer_proxy import *

words_file_name = sys.argv[1]
token_limit = 10
analyzer_port = "http://localhost:8090"

connected, printed = False, False
while not connected:
  try:
    analyzer = Analyzer(analyzer_port)
    connected = True
  except:
    if not printed:
      print("The analyzer_port address provided refused a connection: {}".format(analyzer_port))
      printed = True
    time.sleep(2)

print("Connected to Analyzer")

lex = set(analyzer.get_lexicon())
top_tokens = []
with open(words_file_name) as f:
  for line in f:
    word, count = line.split(",")
    count = int(count.strip())
    if word not in lex:
      if len(top_tokens) < token_limit:
        top_tokens.append((word, count))
        top_tokens.sort(key=lambda x: x[1], reverse=True)
      else:
        if count > top_tokens[-1][1]:
          top_tokens.pop()
          top_tokens.append((word, count))
          top_tokens.sort(key=lambda x: x[1], reverse=True)

pprint(top_tokens)
