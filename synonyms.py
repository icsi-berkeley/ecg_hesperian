import nltk
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from itertools import chain
import re


MORPH_FILE = "ecg_grammars/core/celex.ecgmorph"
TOKEN_FILES = ["ecg_grammars/hesperian/hesperian.tokens",
				"ecg_grammars/research/testing.tokens"]

# To the best of my ability
tag_dict = {'JJ':'Positive', 'JJR':'Comparative', 'JJS':'Superlative',
	'NN':'Singular', 'NNS':'Plural', 'NNP':'Singular', 'NNPS':'Plural',
	'RB':'Positive', 'RBR':'Comparative', 'RBS':'Superlative',
	'VB':'Infinitive', 'VBD':'FirstPersonPastTenseSingular',
	'VBG':'ParticiplePresentTense', 'VBN':'ParticiplePastTense',
	'VBP':'FirstPersonPresentTenseSingular', 'VBZ':'PresentTenseSingularThirdPerson'}


class Synonyms:

	def __init__(self, morph_file, token_files):
		
		self.tokens_in_grammar = set()
		self.lemma_to_word = {} # lemma -> {pos -> word}
		# self.word_to_lemma = {} # word -> ('lemma', [parts of speech])

		# Put all tokens in set
		for token_file in token_files:
			with open(token_file) as tf:
				for line in tf:
					self.tokens_in_grammar.add(line.split('::')[0].rstrip())
		# print(sorted(self.tokens_in_grammar)) - Debugging

		# Create morph dictionary
		with open(morph_file) as mf:
			for line in mf:
				morph = line.split()
				word = morph[0]
				for lemma, tense in zip(morph[1::2], morph[2::2]):
					tense_key = ''.join(sorted(re.split('/|,', tense)))
					if lemma in self.lemma_to_word:
						self.lemma_to_word[lemma][tense_key] = word
					else:
						self.lemma_to_word[lemma] = {tense_key : word}


	def get_synonyms(self, sentence, word):
		tagged = nltk.pos_tag(nltk.word_tokenize(sentence))
		tag = None
		for w, t in tagged:
			if w == word:
				tag = t

		# Default to NoMorphology
		tense = 'NoMorphology'
		if tag in tag_dict:
			tense = tag_dict[tag]

		pos = self.penn_to_wn(tag)
		if not pos:
			return None

		wnl = WordNetLemmatizer()
		wnl.lemmatize(word, pos=pos)

		# # https://stackoverflow.com/questions/19258652/how-to-get-synonyms-from-nltk-wordnet-python
		synonym_synsets = wn.synsets(wnl.lemmatize(word, pos=pos))

		synonyms = set(chain.from_iterable([s.lemma_names() for s in synonym_synsets]))
		
		valid = []
		for synonym in synonyms:
			if synonym in self.tokens_in_grammar:
				if tense in self.lemma_to_word[synonym]:
					valid.append(self.lemma_to_word[synonym][tense])
		return valid


	# Source: https://stackoverflow.com/questions/27591621/nltk-convert-tokenized-sentence-to-synset-format
	def penn_to_wn(self, tag):
		if not tag:
			return None
		elif tag.startswith('J'):
			return wn.ADJ
		elif tag.startswith('N'):
			return wn.NOUN
		elif tag.startswith('R'):
			return wn.ADV
		elif tag.startswith('V'):
			return wn.VERB
		return None



'''
['Comparative', , 'FirstPersonPastTenseSingular',
'FirstPersonPresentTenseSingular', 'Infinitive', 'Meaning', 'NoMorphology',
'ParticiplePastTense', 'ParticiplePresentTense', 'PastTensePlural', 'PastTenseSecondPersonSingular',
'PastTenseSingularThirdPerson', 'Plural', 'PluralPresentTense', 'Positive',
'PresentTenseSecondPersonSingular', 'PresentTenseSingularThirdPerson',
'Singular', 'Superlative']
'''

syn = Synonyms(MORPH_FILE, TOKEN_FILES)
while True:
	sentence = input('sentence > ')
	if sentence == 'q':
			break

	word = input('word >> ')
	if word == 'q':
		break
	
	print(syn.get_synonyms(sentence, word))


'''
Examples:

Great:
'i love my country', 'country'
'i love my countries', 'countries'
'they are attempting', 'attempting'
'big rash', 'big'
'biggest rash', 'biggest'
'pain in tummy', 'tummy'

Problematic:
'he is the quickest person', 'quickest'

Bad:
'guy', 'guy' -> 'cat' ???

'''


