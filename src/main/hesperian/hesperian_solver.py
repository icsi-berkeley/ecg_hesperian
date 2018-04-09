"""

Author: vivekraghuram <vivek.raghuram@berkeley.edu>

A HesperianProblemSolver that extends the CoreProblemSolver in the NLUAS module.

Actions, like "move", should be named by predicate + action type.
Thus: query_move, command_move, etc.
Or: query_be, command_be, etc.

"""
from hesperian_data import HesperianData
import json
from pprint import pprint
from nluas.app.core_solver import CoreProblemSolver
from nluas.utils import *
from nluas.Transport import Transport
import os
import sys
import webbrowser


class BasicHesperianProblemSolver(CoreProblemSolver):
    def __init__(self, args):
        CoreProblemSolver.__init__(self, args)
        self._recent = None
        self._wh = None
        self._terminate = False
        # self.args = []
        self.CNF_query = [] # list of lists, converted to conjunctive normal form for search engine
        self.extracted_information = {}
        # self.around = " AROUND({}) ".format(5) # Config var for how close together the field name is to the value

        self.wiki_address = "Wiki"
        self.transport.subscribe(self.wiki_address, self.wiki_callback)

        self.clarification_templates = self.read_templates(
                                           os.path.dirname(os.path.realpath(__file__)) +
                                           '/clarification_templates.json')

        self.data = HesperianData()

    def wiki_callback(self, request):
        sid = request['sid']
        if not self.data.touch(sid):
            sid = self.data.create_user()
        if 'clarification' in request:
            self.process_clarification(sid, request['clarification'])
        self.transport.send(self.ui_address, {'text': request['query'], 'sid': sid})

    def solve(self, ntuple):
        pprint(ntuple)
        # self.args = []
        self.CNF_query = []
        self.extracted_information = {}
        response = {'sid': ntuple['sid']}
        pred_type = ntuple['predicate_type'] if 'predicate_type' in ntuple else 'unstructured'
        try:
            dispatch = getattr(self, "solve_%s" %pred_type)
            dispatch(ntuple)
            self.merge_user_information(ntuple['sid'])
            self.generate_query(response, ntuple)
            self.generate_clarification(response, ntuple)
            self.transport.send(self.wiki_address, response)
        except AttributeError as e:
            traceback.print_exc()
            message = "I cannot solve a(n) {}.".format(pred_type)
            self.identification_failure(message)

    def merge_user_information(self, sid):
        """Right now this simply overwrites all user info for the extracted fields but in the
           future, it might be important to preserve previous information or set some kind of
           precedence based on specificity of the value. e.g. list of symptoms"""
        for (field, value) in self.extracted_information.items():
            self.data.set_data(sid, field, value)

    def generate_query(self, response, ntuple):
        # self.CNF_query.append([ntuple['original_query']])
        query = []
        if self.CNF_query:
            for clause in self.CNF_query:
                #NOTE:every clause matches empty string to make sure it's satisfiable
                # clause += ["''"]
                query.append("(" + " OR ".join(clause) + ")")
        response['query'] = " OR ".join(query)
        self.data.add_query(ntuple['sid'], ntuple['original_query'], response['query'])

    def assemble_query_elements(self, elems1, elems2, join=" "):
        if type(elems1) != list and type(elems1) != tuple:
            elems1 = [elems1]
        if type(elems2) != list and type(elems2) != tuple:
            elems2 = [elems2]
        return [one + join + two for one in elems1 for two in elems2]

    def generate_clarification(self, response, ntuple):
        """Adds the appropriate information to the response for the wiki to ask a clarification
           question. Currently just asks the first clarification question that matches the
           conditions. In the future it might be more useful to choose the most constrained
           clarification question."""
        for (cname, clarification) in self.clarification_templates.items():
          condition = clarification['condition']
          is_valid = True
          for (key, value) in condition.items():
              if self.data.get_data(ntuple['sid'], key) != value:
                  print("User is {} and condition is {}".format(
                            self.data.get_data(ntuple['sid'], key), value))
                  is_valid = False
                  break
          if is_valid:
              response['clarification'] = clarification
              return

    def process_clarification(self, sid, clarification):
        """Incorporates information from the answer the clarification question into the user
           profile"""
        if clarification['val'] != None:
            self.data.set_data(sid, clarification['field'], clarification['val'])

    def solve_unstructured(self, ntuple):
        if 'descriptorType' in ntuple:
            if ntuple['descriptorType'] == 'symptomDescriptor':
                return self.solve_symptomDescriptor(ntuple)
            elif ntuple['descriptorType'] == 'diseaseDescriptor':
                return self.solve_diseaseDescriptor(ntuple)
            elif ntuple['descriptorType'] == 'treatmentDescriptor':
                return self.solve_treatmentDescriptor(ntuple)
            elif ntuple['descriptorType'] == 'eventDescriptor':
                return self.solve_eventDescriptor(ntuple)
            else:
                return self.solve_basic(ntuple)

    def solve_symptomDescriptor(self, symptomDescriptor):
        symptom = symptomDescriptor['type']
        clause = ["{}".format(symptom)]
        self.extracted_information['symptom'] = symptom
        if 'location' in symptomDescriptor:
            location = self.get_location(symptomDescriptor['location']['objectDescriptor'])
            self.extracted_information['symptom_location'] = location
            clause += self.assemble_query_elements(symptom, location)
        if symptomDescriptor['disease']['objectDescriptor']['type'] != 'disease':
            disease = self.solve_diseaseDescriptor(symptomDescriptor['disease']['objectDescriptor'])
            clause += self.assemble_query_elements(symptom, disease)
        if symptomDescriptor['trigger']['objectDescriptor']['descriptorType'] != 'objectDescriptor':
            trigger = self.solve_unstructured(symptomDescriptor['trigger']['objectDescriptor'])
            clause += self.assemble_query_elements(symptom, trigger)
        if 'duration' in symptomDescriptor:
            duration = self.get_duration(symptomDescriptor['duration']['objectDescriptor'])
            clause += self.assemble_query_elements(symptom, duration)

        self.CNF_query.append(clause)
        return clause

    def solve_diseaseDescriptor(self, diseaseDescriptor):
        disease = diseaseDescriptor['type']
        self.extracted_information['disease'] = disease
        clause = ["{} (disease|symptom|sign)".format(disease),
                  "{}".format(disease)]
        self.CNF_query.append(clause)
        return clause
        # self.args.append(disease)
        # self.args += ["OR", ["symptom", "OR", "sign"]]

    def solve_treatmentDescriptor(self, treatmentDescriptor):
        treatment = treatmentDescriptor['type']
        self.extracted_information['treatment'] = treatment
        clause = ["{} (treatment|medicine|operation)".format(treatment),
                  "{}".format(treatment)]
        self.CNF_query.append(clause)
        return clause

    def solve_patientDescriptor(self, patientDescriptor):
        raise NotImplementedError

    def get_location(self, locationDescriptor):
        location = locationDescriptor['type']
        return location
        # self.args.append(location)

    def get_duration(self, objectDescriptor):
        amount = objectDescriptor['quantity']['amount']['value']
        units = objectDescriptor['quantity']['units']
        return "1..{} {}s".format(amount, units)

    def solve_eventDescriptor(self, eventDescriptor):
        dispatch = getattr(self, "solve_event_%s" %eventDescriptor['eventProcess']['template'].lower())
        return dispatch(eventDescriptor)

    def solve_basic(self, descriptor):
        print("{} defaulted to solve_basic".format(descriptor['descriptorType']))
        clause = ["{}".format(descriptor['type'])]
        self.CNF_query.append(clause)
        return clause

    def solve_query(self, ntuple):
        if 'eventDescriptor' in ntuple:
            eventDescriptor = ntuple['eventDescriptor']
            return self.solve_eventDescriptor(eventDescriptor)

    def solve_event_stasis(self, eventDescriptor):
        # if eventDescriptor['profiledParticipant']['objectDescriptor']['specificWh'] == 'what':
        obj = eventDescriptor['eventProcess']['state']['identical']['objectDescriptor']
        return self.solve_unstructured(obj)

    def solve_event_possprocess(self, eventDescriptor):
        #QUESTION would the possessor be the patient?
        pos_obj = eventDescriptor['eventProcess']['possessed']['objectDescriptor']
        return self.solve_unstructured(pos_obj)

    def solve_event_causeeffect(self, eventDescriptor):
        agent = eventDescriptor['eventProcess']['causalAgent']['objectDescriptor']
        agent_clause = self.solve_unstructured(agent)
        # self.args.append("OR")
        patient = eventDescriptor['eventProcess']['affectedProcess']['protagonist']['objectDescriptor']
        patient_clause = self.solve_unstructured(patient)
        # clause = self.assemble_query_elements(agent_clause, patient_clause,
        #                                       " (affect|effect|cause) ") + \
        #          self.assemble_query_elements(agent_clause, patient_clause)
        # self.CNF_query.append(clause)
        # return clause

if __name__ == "__main__":
    solver = BasicHesperianProblemSolver(sys.argv[1:])
