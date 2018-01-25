"""
Author: seantrott <seantrott@icsi.berkeley.edu>
Similar to a regular UserAgent, but it uses a HesperianSpecializer instead.
"""

from nluas.language.user_agent import *
from hesperian_specializer import *
from nluas.language.spell_checker import *
import sys
import subprocess


class HesperianUserAgent(UserAgent):

    def __init__(self, args):
        UserAgent.__init__(self, args)
        self.spell_checker = SpellChecker(self.analyzer.get_lexicon())

    def initialize_specializer(self):
        self.specializer = HesperianSpecializer(self.analyzer)

    def output_stream(self, tag, message):
        print("{}: {}".format(tag, message))

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
                new_ntuple = self.check_spelling(ntuple['text'])
                if new_ntuple and new_ntuple != "null":
                    self.transport.send(self.solve_destination, new_ntuple)
        elif ntuple['type'] == "clarification":
            descriptor = self.check_spelling(msg)
            self.clarification = False
            new_ntuple = self.clarify_ntuple(ntuple['original'], descriptor)
            self.transport.send(self.solve_destination, new_ntuple)
            self.clarification = False


    def check_spelling(self, msg):
        table = self.spell_checker.spell_check(msg)
        if table:
            checked =self.spell_checker.join_checked(table['checked'])
            if checked != msg:
                ### DEBUGGING: Print corrected message: ###
                # print(self.spell_checker.print_modified(table['checked'], table['modified']))
                return self.process_input(checked)
            else:
                return self.process_input(msg)


if __name__ == "__main__":
    ui = HesperianUserAgent(sys.argv[1:])
