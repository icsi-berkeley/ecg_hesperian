
import csv

all_tokens = set()

with open('tokens.csv') as tokens_file:
	reader = csv.reader(tokens_file)

	# Skip header
	next(reader)
	for token in reader:
		if not token[0].isdigit():
			all_tokens.add(token[0])


with open('hesp_wiki_tokens.csv', 'w') as cleaned_tokens_file:
	writer = csv.writer(cleaned_tokens_file)
	for t in sorted(all_tokens):
		writer.writerow([t])
