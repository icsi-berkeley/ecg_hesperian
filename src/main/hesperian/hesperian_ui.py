"""
Author: vivekraghuram <vivek.raghuram@berkeley.edu>
Similar to a regular UserAgent, but it uses a HesperianSpecializer instead. Includes features for
spell checking and swapping words for synonyms that have tokens in the analyzer.
"""

from nluas.language.user_agent import *
from hesperian_specializer import *
from hesperian_word_checker import *
import sys
import subprocess


class HesperianUserAgent(UserAgent):

    def __init__(self, args):
        UserAgent.__init__(self, args)
        self.word_checker = HesperianWordChecker(self.analyzer.get_lexicon())

    def initialize_specializer(self):
        self.specializer = HesperianSpecializer(self.analyzer)

    def output_stream(self, tag, message):
        print("{}: {}".format(tag, message))

    def callback(self, ntuple):
        """ Process information from ProblemSolver """
        msg = ntuple['text']
        if self.is_quit(ntuple):
            self.close()
        elif msg != None and msg != "":
            new_ntuple = self.process_input(msg)
            if new_ntuple and new_ntuple != "null":
                new_ntuple['original_query'] = msg
                new_ntuple['sid'] = ntuple['sid']
                self.transport.send(self.solve_destination, new_ntuple)
        # super(HesperianUserAgent, self).callback(ntuple)

    def text_callback(self, ntuple):
        """ Processes text from a SpeechAgent. """
        specialize = True
        msg = ntuple['text']
        if self.is_quit(ntuple):
            self.close()
        elif ntuple['type'] == "standard":
            if msg == None or msg == "":
                specialize = False
            elif msg.lower() == "d":
                self.specializer.set_debug()
                specialize = False
            elif specialize:
                new_ntuple = self.process_input(ntuple['text'])
                if new_ntuple and new_ntuple != "null":
                    self.transport.send(self.solve_destination, new_ntuple)
        elif ntuple['type'] == "clarification":
            descriptor = self.process_input(msg)
            self.clarification = False
            new_ntuple = self.clarify_ntuple(ntuple['original'], descriptor)
            self.transport.send(self.solve_destination, new_ntuple)
            self.clarification = False


    def process_input(self, msg):
      table = self.word_checker.check(msg)
      if table:
        msg = self.word_checker.join_checked(table['checked'])
      return super(HesperianUserAgent, self).process_input(msg)

if __name__ == "__main__":
    ui = HesperianUserAgent(sys.argv[1:])
