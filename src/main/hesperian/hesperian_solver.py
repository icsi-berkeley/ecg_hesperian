"""

Author: vivekraghuram <vivek.raghuram@berkeley.edu>

A HesperianProblemSolver that extends the CoreProblemSolver in the NLUAS module.

Actions, like "move", should be named by predicate + action type.
Thus: query_move, command_move, etc.
Or: query_be, command_be, etc.

"""
from nluas.app.core_solver import *
from nluas.utils import *
import sys
from threading import Thread, Lock
from functools import wraps
from nluas.Transport import Transport
import json
import time
import webbrowser

class BasicHesperianProblemSolver(CoreProblemSolver):
    def __init__(self, args):
        CoreProblemSolver.__init__(self, args)
        self._recent = None
        self._wh = None
        self._terminate = False

    def solve(self, ntuple):
        print(ntuple)
        if self.check_for_clarification(ntuple):
            self.request_clarification(ntuple=ntuple)
        else:
            self.ntuple = ntuple
            predicate_type = 'unstructured'
            if 'predicate_type' in ntuple:
                predicate_type = ntuple['predicate_type']
            try:
                dispatch = getattr(self, "solve_%s" %predicate_type)
                dispatch(ntuple)
                self.broadcast()
                self.p_features = None # Testing, took it out from route_action
            except AttributeError as e:
                traceback.print_exc()
                message = "I cannot solve a(n) {}.".format(predicate_type)
                self.identification_failure(message)

    def solve_unstructured(self, ntuple):
        print("solve_unstrctured")
        if ntuple['descriptorType'] == 'symptomDescriptor':
                self.solve_symptom(ntuple)
        elif ntuple['descriptorType'] == 'diseaseDescriptor':
                self.solve_disease(ntuple)
        else:
            self.solve_basic(ntuple)

    def solve_symptom(self, ntuple):
        print("solve_symptom")
        args = []
        args.append(ntuple['type'])
        #print(ntuple['location'])
        if ntuple['location']['objectDescriptor']['type'] != 'bodyPart':
            args.append(ntuple['location']['objectDescriptor']['type'])
        if ntuple['disease']['objectDescriptor']['type'] != 'disease':
            args.append(ntuple['disease']['objectDescriptor']['type'])
        self.generate_url(args)

    def solve_disease(self, ntuple):
        print("solve_disease")
        args = []
        args.append(ntuple['type'])
        self.generate_url(args)

    def solve_basic(self, ntuple):
        print("solve_basic")
        args = []
        args.append(ntuple['type'])
        self.generate_url(args)

    def solve_query(self, ntuple):
        print("solve_query")
        args = []
        args.append(ntuple['eventDescriptor']['eventProcess']['possessed']['objectDescriptor']['type'])
        args.append(ntuple['eventDescriptor']['eventProcess']['possessed']['objectDescriptor']['possessor']['objectDescriptor']['gender'])
        self.generate_url(args)

    # def solve_modal(self, ntuple):
    #     print("solve_modal")
    #     args = []
    #     args.append(ntuple['type'])
    #     self.generate_url(args)

    def generate_url(self, args):
        url = "http://hesperian.org/"
        if args:
            url += "?s="
            for arg in args:
                url += arg + "+"
            url = url[:-1] #remove trailing '+'
        self.open_url(url)

    def open_url(self, url):
        webbrowser.open(url)

if __name__ == "__main__":
    solver = BasicHesperianProblemSolver(sys.argv[1:])
