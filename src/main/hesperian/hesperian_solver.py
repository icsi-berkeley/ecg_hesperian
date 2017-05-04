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
        if ntuple['schema'] == 'Symptom':
            self.solve_symptom(ntuple)

    def solve_symptom(self, ntuple):
        print(ntuple)
        args = []
        self.generate_url(args)

    def solve_serial(self, parameters, predicate):
        """
        Solves a serial event
        """
        self.route_action(parameters['process1'], predicate)
        self.route_action(parameters['process2'], predicate)

    def solve_command(self, ntuple):
        """
        Solves a command
        """
        parameters = ntuple['eventDescriptor']
        self.route_event(parameters, "command")

    def generate_url(self, args):
        url = "http://hesperian.org/"
        if args:
            url += "?s="
            for arg in args:
                url += "+" + arg
        self.open_url(url)

    def open_url(self, url):
        webbrowser.open(url)

if __name__ == "__main__":
    solver = BasicHesperianProblemSolver(sys.argv[1:])
