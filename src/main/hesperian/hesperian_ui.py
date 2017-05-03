"""
Author: seantrott <seantrott@icsi.berkeley.edu>
Similar to a regular UserAgent, but it uses a HesperianSpecializer instead.
"""

from nluas.language.user_agent import *
from hesperian_specializer import *
import sys
import subprocess


class HesperianUserAgent(UserAgent):

    def __init__(self, args):
        UserAgent.__init__(self, args)

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
                new_ntuple = self.process_input(ntuple['text'])
                if new_ntuple and new_ntuple != "null":
                    self.transport.send(self.solve_destination, new_ntuple)
        elif ntuple['type'] == "clarification":
            descriptor = self.process_input(msg)
            self.clarification = False
            new_ntuple = self.clarify_ntuple(ntuple['original'], descriptor)
            self.transport.send(self.solve_destination, new_ntuple)
            self.clarification = False

if __name__ == "__main__":
    ui = HesperianUserAgent(sys.argv[1:])
