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

class BasicHesperianProblemSolver(CoreProblemSolver):
    def __init__(self, args):
        CoreProblemSolver.__init__(self, args)
        self._recent = None
        self._wh = None
        self._terminate = False
        self._wiki_knowledge = {
            "malaria": {"fever": "Oh no! you have a fever from malaria", "default": "oh no you have malaria!"},
            "pain": {"abdomen": "ouch you have abdomen pain", "default": "oh no something hurts"},
            "fever": {"default": "oh no you have a fever!"},
            "default": "you good!"
        }

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
        args = []
        if "givenness" in ntuple['disease']['objectDescriptor']:
            args.append(ntuple['disease']['objectDescriptor']['type'])
        if "givenness" in ntuple['symptom']['objectDescriptor']:
            args.append(ntuple['symptom']['objectDescriptor']['type'])
        if "givenness" in ntuple['experiencer']['objectDescriptor']:
            args.append(ntuple['experiencer']['objectDescriptor']['type'])
        if "givenness" in ntuple['location']['objectDescriptor']:
            args.append(ntuple['location']['objectDescriptor']['type'])

        response = self._wiki_knowledge
        for arg in args:
            response = response[arg]

        if isinstance(response, dict):
            response = response["default"]

        print(response)


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


if __name__ == "__main__":
    solver = BasicHesperianProblemSolver(sys.argv[1:])
