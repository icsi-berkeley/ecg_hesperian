"""
@author: <seantrott@icsi.berkeley.edu>
A simple program to output n-tuples using Analyzer+Specializer. Not reliant on any packages other than Jython.
"""
from hesperian_specializer import *
from nluas.ntuple_decoder import *
import traceback

decoder = NtupleDecoder()

analyzer = Analyzer("http://localhost:8090")
hs = HesperianSpecializer(analyzer)

try:
    input = raw_input
except NameError:
    pass

while True:
    text = input("> ")
    if text == "q":
        quit()
    elif text == "d":
        hs.debug_mode = True
    else:
        try:
            semspecs = analyzer.parse(text)
            for fs in semspecs:
                try:
                    ntuple = hs.specialize(fs)
                    pprint(ntuple)
                    #decoder.pprint_ntuple(ntuple)
                    break
                except Exception as e:
                    traceback.print_exc()
                    print(e)
        except Exception as e:
            traceback.print_exc()
            print(e)
