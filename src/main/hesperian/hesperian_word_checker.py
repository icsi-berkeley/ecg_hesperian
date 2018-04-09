"""
Author: vivekraghuram <vivek.raghuram@berkeley.edu>
Combines the features of spell checking and swapping for synonyms with a token.
------
See LICENSE.txt for licensing information.
------
"""

import enchant
import string
from nluas.language.spell_checker import Color
from IPython import embed

class HesperianWordChecker(object):

  def __init__(self, lexicon):
    self.general = enchant.Dict("en_US")

    self.lexicon = enchant.pypwl.PyPWL()
    self.load_lexicon(lexicon)

    self.synonym_map = self.load_synonyms()

    self.translate_table = dict()

    for i in string.punctuation:
      self.translate_table[ord(i)] = " " + i + " "


  def load_lexicon(self, lexicon):
    for word in lexicon:
      self.lexicon.add(word)


  def load_synonyms(self):
    """
      Loads data structure/file of synonyms. Looks for occurences of tokens and creates a map
      from all synonyms of that token to the token.
    """
    # TODO: implement this
    return {"crate": "box"}


  def check(self, sentence):
    split = sentence.translate(self.translate_table).split()
    checked = []
    modified = []
    for word in split:
      checked_word, is_modified = self.check_word(word)
      checked.append(checked_word)
      modified.append(is_modified)
    return {'checked': checked, 'modified': modified}


  def check_word(self, word):
    if self.lexicon.check(word):
      return word, False
    if self.general.check(word) and word in self.synonym_map:
      return self.synonym_map[word], True

    lexicon_suggestions = self.lexicon.suggest(word)
    if len(lexicon_suggestions) > 0:
      return lexicon_suggestions[0], True

    general_suggestions = self.general.suggest(word)
    if len(general_suggestions) > 0:
      for suggestion in general_suggestions:
        if suggestion in self.synonym_map:
          return self.synonym_map[suggestion], True

    return False

  def join_checked(self, checked):
    corrected = ""
    for word in checked:
      if word in string.punctuation:
        corrected += word
      else:
        corrected += " " + word
    return corrected.strip()


  def print_modified(self, checked, modified):
    corrected = ""
    index = 0
    while index < len(checked):
      if checked[index] in string.punctuation:
        corrected += checked[index]
      else:
        if modified[index]:
          corrected += " " + Color.RED + checked[index] + Color.END
        else:
          corrected += " " + checked[index]
          index += 1
    return corrected.strip()
