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
from pprint import pprint

class BasicHesperianProblemSolver(CoreProblemSolver):
    def __init__(self, args):
        CoreProblemSolver.__init__(self, args)
        self._recent = None
        self._wh = None
        self._terminate = False
        self.args = []


    def solve(self, ntuple):
        pprint(ntuple)
        self.args = []
        if self.check_for_clarification(ntuple):
            self.request_clarification(ntuple=ntuple)
        else:
            self.ntuple = ntuple
            pred_type = ntuple['predicate_type'] if 'predicate_type' in ntuple else 'unstructured'
            try:
                dispatch = getattr(self, "solve_%s" %pred_type)
                dispatch(ntuple)
                self.generate_url()
            except AttributeError as e:
                traceback.print_exc()
                message = "I cannot solve a(n) {}.".format(pred_type)
                self.identification_failure(message)

    def solve_unstructured(self, ntuple):
        print("solve_unstructured")
        if 'descriptorType' in ntuple:
            if ntuple['descriptorType'] == 'symptomDescriptor':
                self.solve_symptom(ntuple)
            elif ntuple['descriptorType'] == 'diseaseDescriptor':
                self.solve_disease(ntuple)
            elif ntuple['descriptorType'] == 'treatmentDescriptor':
                self.solve_treatment(ntuple)
            elif ntuple['descriptorType'] == 'eventDescriptor':
                self.solve_event(ntuple)
            else:
                self.solve_basic(ntuple)

    def solve_symptom(self, ntuple):
        print("solve_symptom")
        self.args.append(ntuple['type'])
        if ntuple['location']['objectDescriptor']['type'] != 'bodyPart':
            self.solve_location(ntuple['location']['objectDescriptor'])
        if ntuple['disease']['objectDescriptor']['type'] != 'disease':
            self.solve_disease(ntuple['disease']['objectDescriptor'])
        if ntuple['trigger']['objectDescriptor']['descriptorType'] != 'objectDescriptor':
            self.solve_unstructured(ntuple['trigger']['objectDescriptor'])

    def solve_disease(self, diseaseDescriptor):
        print("solve_disease")
        self.args.append(diseaseDescriptor['type'])
        self.args += ["OR", ["symptom", "OR", "sign"]]

    def solve_treatment(self, treatmentDescriptor):
        self.args.append(treatmentDescriptor['type'])

    def solve_location(self, locationDescriptor):
        self.args.append(locationDescriptor['type'])

    def solve_event(self, eventDescriptor):
        dispatch = getattr(self, "solve_event_%s" %eventDescriptor['eventProcess']['template'].lower())
        dispatch(eventDescriptor)

    def solve_basic(self, ntuple):
        print("solve_basic")
        self.args.append(ntuple['type'])

    def solve_query(self, ntuple):
        print("solve_query")
        if 'eventDescriptor' in ntuple:
            eventDescriptor = ntuple['eventDescriptor']
            self.solve_event(eventDescriptor)

    def solve_event_stasis(self, eventDescriptor):
        # if eventDescriptor['profiledParticipant']['objectDescriptor']['specificWh'] == 'what':
        obj = eventDescriptor['eventProcess']['state']['identical']['objectDescriptor']
        self.solve_unstructured(obj)

    def solve_event_possprocess(self, eventDescriptor):
        pos_obj = eventDescriptor['eventProcess']['possessed']['objectDescriptor']
        self.solve_unstructured(pos_obj)

    def solve_event_causeeffect(self, eventDescriptor):
        agent = eventDescriptor['eventProcess']['causalAgent']['objectDescriptor']
        self.solve_unstructured(agent)
        self.args.append("OR")
        patient = eventDescriptor['eventProcess']['affectedProcess']['protagonist']['objectDescriptor']
        self.solve_unstructured(patient)

    def generate_url(self):
        url = "http://en.hesperian.org/w/index.php"
        if self.args:
            url += "?search="
            for arg in self.args:
                if isinstance(arg, list):
                    arg = "(" + "+".join(arg) + ")"
                url += arg + "+"
            url = url[:-1] #remove trailing '+'
        self.open_url(url)

    def open_url(self, url):
        # may cause errors due to this bug on macs: https://bugs.python.org/issue30392
        # webbrowser.open_new_tab(url)

        # temporary fix:
        ff = webbrowser.get('firefox')
        ff.open_new_tab(url)

if __name__ == "__main__":
    solver = BasicHesperianProblemSolver(sys.argv[1:])
