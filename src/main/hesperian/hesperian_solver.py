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
from itertools import combinations
from nluas.language.analyzer_proxy import *
import os
import sys
import webbrowser

def depth(f):
    def wrapper(*args, **kwargs):
        slf = args[0]
        slf.depth += 1
        rv = f(*args, **kwargs)
        slf.depth -= 1
        return rv
    return wrapper

class ListedDictionary(dict):
    """
    Values in dictionary will be appended to lists at every key. The values will be paired with
    the depth at which it was extracted in a tuple.
    e.g. {key1: [(value1, depth1)], key2: [(value2, depth2), (value3, depth3)]}
    """
    def __init__(self, slf):
        self.slf = slf
        super(ListedDictionary, self).__init__(self)

    def __setitem__(self, key, value):
        if value == None:
            return
        if key in self:
            lst, dup, remove = self[key], False, None
            for pair in lst:
                v, depth = pair
                if v == value and depth <= self.slf.depth:
                    dup = True
                elif v == value:
                    remove = (v, depth)
            if not dup: # don't append duplicates
                lst.append((value, self.slf.depth))
            if remove:
                lst.remove(remove)
            super(ListedDictionary, self).__setitem__(key, lst)
        else:
            super(ListedDictionary, self).__setitem__(key, [(value, self.slf.depth)])

class BasicHesperianProblemSolver(CoreProblemSolver):
    def __init__(self, args):
        CoreProblemSolver.__init__(self, args)
        self._recent = None
        self._wh = None
        self._terminate = False
        self.depth = 0
        self.extracted_information = ListedDictionary(self)

        self.wiki_address = "Wiki"
        self.transport.subscribe(self.wiki_address, self.wiki_callback)

        self.clarification_templates = self.read_templates(
                                           os.path.dirname(os.path.realpath(__file__)) +
                                           '/clarification_templates.json')

        self.data = HesperianData()
        self.analyzer_port = "http://localhost:8090"
        self.analyzer = Analyzer(self.analyzer_port)

    def wiki_callback(self, request):
        print(request)
        sid = request['sid']
        synonyms = False
        if not self.data.touch(sid):
            sid = self.data.create_user()
        if request['clarification']:
            self.process_clarification(sid, request['clarification'])
        elif request['synonyms']:
            synonyms = []
            for swap in request['synonyms']:
                old, new = swap.split('>')
                request['query'] = request['query'].replace(old, new)
                synonyms.append((old, new))
        self.transport.send(self.ui_address, {'text': request['query'], 'sid': sid, 'synonyms': synonyms})

    def solve(self, ntuple):
        pprint(ntuple)
        self.extracted_information = ListedDictionary(self)
        response = {'sid': ntuple['sid']}
        if 'FAILURE_TYPE' in ntuple:
            return self.process_failure(ntuple, response)
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

    def process_failure(self, ntuple, response):
        if ntuple['FAILURE_TYPE'] == 'UNKNOWN_WORD':
            response['error'] = "Unknown words: {}. Please rephrase your query.".format(ntuple['FAILURES'])
            response['failures'] = ntuple['FAILURES']
            response['failure_type'] = ntuple['FAILURE_TYPE']
        elif ntuple['FAILURE_TYPE'] == 'CANNOT_ANALYZE':
            response['error'] = "Analysis of query failed."
            response['failure_type'] = ntuple['FAILURE_TYPE']
        self.transport.send(self.wiki_address, response)

    def merge_user_information(self, sid):
        """Right now this simply overwrites all user info for the extracted fields but in the
           future, it might be important to preserve previous information or set some kind of
           precedence based on specificity of the value. e.g. list of symptoms"""
        pprint(self.extracted_information)
        for (field, value) in self.extracted_information.items():
            value = value[0] # TODO: should set data for everything in list but will do later
            self.data.set_data(sid, field, value[0])

    def generate_query(self, response, ntuple):
        self.add_user_information(ntuple['sid'])
        fragments = []
        for key, values in self.extracted_information.items():
            spices = self.get_spices(key)
            min_importance = 1.0 # tracks the minimal importance gives to all values
            for (value, depth) in values:
                importance = self.get_importance(key, value, depth) * 0.9 ** (len(values) - 1)
                query_term = self.get_query_term(key, value, depth)
                min_importance = min(importance, min_importance)
                fragments.append((key, query_term, importance))
            for spice in spices:
                fragments.append((key + "_spice", spice, min_importance))

        query_combinations = self.get_query_combinations(fragments)
        response['queries'] = [text for (text, score) in query_combinations]
        self.data.add_query(ntuple['sid'], ntuple['original_query'], response['queries'])

    def get_importance(self, key, value, depth):
        """Generates an integer 'importance' value to help in weighting query terms"""
        multiplier = 0.8 ** depth if depth > 1 else 1.0
        base = 0.0
        if key in ['condition', 'symptom', 'disease', 'treatment']:
          base += 5
        elif key in ['gender', 'age'] or 'location' in key:
          base += 4
        elif 'condition' in key or 'symptom' in key or 'disease' in key or 'treatment' in key:
          base += 3
        else:
          base += 2
        return multiplier * base

    def get_query_term(self, key, value, depth):
        if key == 'gender' and value == 'female':
            return '"Where Women Have No Doctor"'
        return value

    def get_spices(self, key):
        """Adds extra information based on the keys of a field"""
        spices = []
        if key == 'disease':
            spices.append('(disease|symptom|sign)')
        elif key == 'symptom':
            spices.append('(signs|symptoms)')
        elif key == 'treatment':
            spices.append('(treatment|medicine|operation)')
        return spices

    def get_query_combinations(self, fragments):
        limit = 20 # maximum number of queries to send
        query_combinations = []
        print(fragments)
        for i in range(len(fragments)):
            for comb in combinations(fragments, i + 1):
                valid, usable = True, {}
                for fragment in comb:
                    if len(fragment[0].split("_")) == 1:
                        if fragment[0] in usable:
                            txt, score = usable[fragment[0]]
                            usable[fragment[0]] = (txt + " " + fragment[1], fragment[2] + score)
                        else:
                            usable[fragment[0]] = (fragment[1], fragment[2])
                for fragment in comb:
                    if fragment[0].split("_")[0] not in usable:
                        valid = False
                        break
                    elif len(fragment[0].split("_")) > 1:
                        key = fragment[0].split("_")[0]
                        txt, score = usable[key]
                        usable[key] = (txt + " " + fragment[1], fragment[2] + score)
                if valid:
                    query = ["", 0]
                    for key in usable:
                        query[0] += usable[key][0] + " "
                        query[1] += usable[key][1]
                    query_combinations.append(tuple(query))

        query_combinations.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
        print(len(query_combinations))
        return query_combinations[0:limit]

    def assemble_query_elements(self, elems1, elems2, join=" "):
        if elems1 == None or elems2 == None or len(elems1) == 0 or len(elems2) == 0:
            return []
        assert(type(elems1) == list)
        assert(type(elems2) == list)
        if type(elems1) != list and type(elems1) != tuple:
            elems1 = [elems1]
        if type(elems2) != list and type(elems2) != tuple:
            elems2 = [elems2]
        return [one.strip() + join + two.strip() for one in elems1 for two in elems2]

    def add_user_information(self, sid):
        """ Adds previously saved user information to the extracted information """
        if 'gender' not in self.extracted_information and self.data.get_data(sid, 'gender'):
            self.extracted_information['gender'] = self.data.get_data(sid, 'gender')

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
                    # print("User is {} and condition is {}".format(
                    #           self.data.get_data(ntuple['sid'], key), value))
                    is_valid = False
                    break
            if is_valid:
                response['clarification'] = clarification
                return

    def process_clarification(self, sid, clarification):
        """Incorporates information from the answer the clarification question into the user
           profile"""
        if clarification['val'] != None:
            self.data.set_data(sid, clarification['field'].lower(), clarification['val'].lower())


    @depth
    def solve_unstructured(self, ntuple):
        if 'descriptorType' in ntuple:
            if 'specificWh' in ntuple:
                self.extracted_information['specificWh'] = ntuple['specificWh']
            if 'modifier' in ntuple:
                self.solve_unstructured(ntuple['modifier']['objectDescriptor'])
            if 'property' in ntuple:
                self.solve_unstructured(ntuple['property']['objectDescriptor'])
            if 'locationDescriptor' in ntuple:
                self.solve_unstructured(ntuple['locationDescriptor']['objectDescriptor'])

            if ntuple['descriptorType'] in ['conditionDescriptor', 'symptomDescriptor', 'diseaseDescriptor']:
                return self.solve_conditionDescriptor(ntuple)
            elif ntuple['descriptorType'] == 'treatmentDescriptor':
                return self.solve_treatmentDescriptor(ntuple)
            elif ntuple['descriptorType'] == 'patientDescriptor':
                return self.solve_patientDescriptor(ntuple)
            elif ntuple['descriptorType'] == 'eventDescriptor':
                return self.solve_eventDescriptor(ntuple)
            elif ntuple['descriptorType'] == 'hesperianBagDescriptor':
                return self.solve_hesperianBagDescriptor(ntuple)
            else:
                return self.solve_basic(ntuple)

    def solve_conditionDescriptor(self, conditionDescriptor):
        descriptorType = conditionDescriptor['descriptorType']
        if 'type' in conditionDescriptor:
          condition = conditionDescriptor['type']
        else:
          condition = None

        if descriptorType == 'conditionDescriptor':
            type = 'condition'
            if condition != 'conditionType':
                self.extracted_information['condition'] = condition
        elif descriptorType == 'symptomDescriptor':
            type = 'symptom'
            if condition != 'symptomType':
                self.extracted_information['symptom'] = condition
            if 'disease' in conditionDescriptor:
                self.solve_unstructured(conditionDescriptor['disease']['objectDescriptor'])
        elif descriptorType == 'diseaseDescriptor':
            type = 'disease'
            if condition != 'diseaseType':
                self.extracted_information['disease'] = condition
            if 'symptom' in conditionDescriptor:
                self.solve_unstructured(conditionDescriptor['symptom']['objectDescriptor'])
        else:
            raise Error('Should never reach this point')

        if 'trigger' in conditionDescriptor:
            self.solve_unstructured(conditionDescriptor['trigger']['objectDescriptor'])
        if 'patient' in conditionDescriptor:
            self.solve_unstructured(conditionDescriptor['patient']['objectDescriptor'])
        if 'property' in conditionDescriptor:
            self.solve_unstructured(conditionDescriptor['property']['objectDescriptor'])

        if 'location' in conditionDescriptor:
            location = self.get_location(conditionDescriptor['location']['objectDescriptor'])
            if location:
                self.extracted_information['{}_location'.format(type)] = location
        if 'duration' in conditionDescriptor:
            duration = self.get_duration(conditionDescriptor['duration']['objectDescriptor'])
            if duration:
                self.extracted_information['{}_duration'.format(type)] = duration
        if 'intensityScale' in conditionDescriptor:
            intensity = "(bad|severe)" if conditionDescriptor['intensityScale'] > 0.5 else "mild"
            self.extracted_information['{}_intensity'.format(type)] = intensity
        if 'bodyPart2' in conditionDescriptor:
            self.extracted_information['{}_location'.format(type)] = conditionDescriptor['bodyPart2']


    def solve_treatmentDescriptor(self, treatmentDescriptor):
        if 'type' in treatmentDescriptor:
          treatment = treatmentDescriptor['type']
          if treatment not in ['treatmentType', 'drugType', 'procedureType']:
              self.extracted_information['treatment'] = treatment

        if 'drug' in treatmentDescriptor:
            self.solve_unstructured(treatmentDescriptor['drug']['objectDescriptor'])
        if 'patient' in treatmentDescriptor:
            self.solve_unstructured(treatmentDescriptor['patient']['objectDescriptor'])
        if 'condition' in treatmentDescriptor:
            self.solve_unstructured(treatmentDescriptor['condition']['objectDescriptor'])

        if 'location' in treatmentDescriptor:
            location = self.get_location(treatmentDescriptor['location']['objectDescriptor'])
            if location:
                self.extracted_information['treatment_location'] = location
        if 'bodyPart2' in treatmentDescriptor:
            self.extracted_information['treatment_location'] = treatmentDescriptor['bodyPart2']


    def solve_patientDescriptor(self, patientDescriptor):
        if 'gender' in patientDescriptor and patientDescriptor['gender'] != 'genderValues':
            self.extracted_information['gender'] = patientDescriptor['gender']
        if 'age' in patientDescriptor and patientDescriptor['age'] != 'ageGroup':
            self.extracted_information['age'] = patientDescriptor['age'][0:-5] # removes the 'Group' off the end
        if 'numericalAge' in patientDescriptor:
            amount = patientDescriptor['numericalAge']['quantity']['amount']['value']
            units = patientDescriptor['numericalAge']['quantity']['units']
            # TODO: Convert to an age group and add to clause
            self.extracted_information['numerical age'] = amount + " " + units

    # not decorated because depth does not matter
    def solve_hesperianBagDescriptor(self, hesperianBagDescriptor):
        self.solve_unstructured(hesperianBagDescriptor['this']['objectDescriptor'])
        if 'next' in hesperianBagDescriptor:
            self.solve_unstructured(hesperianBagDescriptor['next']['hesperianBagDescriptor'])

    def get_location(self, locationDescriptor):
        location = locationDescriptor['type']
        if location != 'bodyPart2':
            if 'side' in locationDescriptor:
                #NOTE: currently cannot handle serial adjectives (e.g. lower left side) due to specializer
                location = locationDescriptor['side'][0:-4] + " " + location
            if 'feeling' in locationDescriptor:
                location = locationDescriptor['feeling'] + " " + location #TODO: Store this in an actual field
            if 'hardness' in locationDescriptor:
                hardness = 'hard' if locationDescriptor['hardness'] > 0.5 else 'soft'
                location = hardness + " " + location #TODO: store this in an actual field
            return location

    def get_duration(self, objectDescriptor):
        amount = objectDescriptor['quantity']['amount']['value']
        units = objectDescriptor['quantity']['units']
        if amount and units:
            return "1..{} {}s".format(amount, units)

    @depth
    def solve_eventDescriptor(self, eventDescriptor):
        if 'eventProcess' in eventDescriptor:
            dispatch = getattr(self, "solve_event_%s" %eventDescriptor['eventProcess']['template'].lower())
        else:
            dispatch = getattr(self, "solve_event_%s" %eventDescriptor['template'].lower())
        return dispatch(eventDescriptor)

    @depth
    def solve_basic(self, descriptor):
        print("{} defaulted to solve_basic".format(descriptor['descriptorType']))
        if 'type' in descriptor and descriptor['type'] not in ['person', 'agent']:
            self.extracted_information['basicType'] = "{}".format(descriptor['type'])

    @depth
    def solve_query(self, ntuple):
        if 'eventDescriptor' in ntuple:
            eventDescriptor = ntuple['eventDescriptor']
            return self.solve_eventDescriptor(eventDescriptor)
        else:
            raise Error('Unable to solve query, no eventDescriptor')

    @depth
    def solve_event_stasis(self, eventDescriptor):
        # if eventDescriptor['profiledParticipant']['objectDescriptor']['specificWh'] == 'what':
        self.solve_unstructured(eventDescriptor['profiledParticipant']['objectDescriptor'])
        obj = eventDescriptor['eventProcess']['state']['identical']['objectDescriptor']
        return self.solve_unstructured(obj)

    @depth
    def solve_event_possprocess(self, eventDescriptor):
        #QUESTION would the possessor be the patient?
        pos_obj = eventDescriptor['eventProcess']['possessed']['objectDescriptor']
        return self.solve_unstructured(pos_obj)

    @depth
    def solve_event_causeeffect(self, eventDescriptor):
        agent = eventDescriptor['eventProcess']['causalAgent']['objectDescriptor']
        self.solve_unstructured(agent)
        patient = eventDescriptor['eventProcess']['affectedProcess']['protagonist']['objectDescriptor']
        self.solve_unstructured(patient)
        self.extracted_information['actionary'] = eventDescriptor['eventProcess']['actionary']

    @depth
    def solve_event_causalaction(self, eventDescriptor):
        cause = eventDescriptor['eventProcess']['protagonist']['objectDescriptor']
        effect = eventDescriptor['eventProcess']['effect']['eventRDDescriptor']
        self.solve_unstructured(cause)
        self.solve_unstructured(effect)
        self.extracted_information['actionary'] = eventDescriptor['eventProcess']['actionary']

    @depth
    def solve_event_objecttransfer(self, eventDescriptor):
        self.extracted_information['actionary'] = eventDescriptor['eventProcess']['actionary']
        self.solve_eventDescriptor(eventDescriptor['eventProcess']['process1'])
        self.solve_eventDescriptor(eventDescriptor['eventProcess']['process2'])
        self.solve_unstructured(eventDescriptor['eventProcess']['theme']['objectDescriptor'])
        self.solve_unstructured(eventDescriptor['profiledParticipant']['objectDescriptor'])

    @depth
    def solve_event_forceapplication(self, eventDescriptor):
        self.extracted_information['actionary'] = eventDescriptor['actionary']
        self.solve_unstructured(eventDescriptor['actedUpon']['objectDescriptor'])
        self.solve_unstructured(eventDescriptor['protagonist']['objectDescriptor'])

    @depth
    def solve_event_abortionprocess(self, eventDescriptor):
        self.extracted_information['actionary'] = eventDescriptor['eventProcess']['actionary']
        self.solve_unstructured(eventDescriptor['eventProcess']['condition']['objectDescriptor'])
        self.solve_unstructured(eventDescriptor['eventProcess']['patient']['objectDescriptor'])
        self.solve_unstructured(eventDescriptor['eventProcess']['treatment']['objectDescriptor'])

    @depth
    def solve_event_treatmentprocess(self, eventDescriptor):
        self.extracted_information['actionary'] = eventDescriptor['eventProcess']['actionary']
        self.solve_unstructured(eventDescriptor['eventProcess']['condition']['objectDescriptor'])
        self.solve_unstructured(eventDescriptor['eventProcess']['patient']['objectDescriptor'])
        self.solve_unstructured(eventDescriptor['eventProcess']['treatment']['objectDescriptor'])

if __name__ == "__main__":
    solver = BasicHesperianProblemSolver(sys.argv[1:])
