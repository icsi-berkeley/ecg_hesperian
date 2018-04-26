import sys
import string
from collections import Counter

infile = sys.argv[1]
outfile = sys.argv[2]
token_counts = Counter()

with open(infile) as f:
  for line in f:
    token = line.strip().lower()
    if not any(c in string.punctuation or c.isdigit() for c in token):
      token_counts[token] += 1

with open(outfile, 'w+') as f:
  for token in token_counts:
    f.write("{},{}\n".format(token, token_counts[token]))
