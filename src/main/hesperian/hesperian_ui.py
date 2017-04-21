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

if __name__ == "__main__":
    ui = HesperianUserAgent(sys.argv[1:])
