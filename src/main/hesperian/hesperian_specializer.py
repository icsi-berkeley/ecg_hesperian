"""
Author: vivekraghuram <vivek.raghuram@berkeley.edu>
"""

from nluas.language.core_specializer import *
import os

dir_name = os.path.dirname(os.path.realpath(__file__))


class HesperianSpecializer(CoreSpecializer):

    def __init__(self, analyzer_port):
        CoreSpecializer.__init__(self, analyzer_port)

        self.parameter_templates = {}
        self.mood_templates = {}
        self.descriptor_templates = {}
        self.event_templates = {}
        self.initialize_templates()

    def initialize_templates(self):
        self.parameter_templates = self.read_templates(
            os.path.join(dir_name, "parameter_templates.json"))
        self.mood_templates = self.read_templates(
            os.path.join(dir_name, "mood_templates.json"))
        self.descriptor_templates = self.read_templates(
            os.path.join(dir_name, "descriptors.json"))
        self.event_templates = self.read_templates(
            os.path.join(dir_name, "event_templates.json"))

    def get_objectDescriptor(self, item, resolving=False):
        """ Override to use correct descriptors for symptoms, diseases and drugs """
        returned, template = {}, {}

        if "pointers" not in item.__dir__():
            item.pointers = self.invert_pointers(item)
        if self.analyzer.issubtype("SCHEMA", item.type(), "ConjRD"):
            returned = self.get_conjRDDescriptor(item, resolving)


        if self.analyzer.issubtype("SCHEMA", item.type(), "Symptom"):
            returned["descriptorType"] = "symptomDescriptor"
            template = self.descriptor_templates['symptomDescriptor']
        elif self.analyzer.issubtype("SCHEMA", item.type(), "Disease"):
            returned["descriptorType"] = "diseaseDescriptor"
            template = self.descriptor_templates['diseaseDescriptor']
        elif self.analyzer.issubtype("SCHEMA", item.type(), "Drug"):
            returned["descriptorType"] = "treatmentDescriptor"
            template = self.descriptor_templates['treatmentDescriptor']
        else:
            returned["descriptorType"] = "objectDescriptor"
            template = self.descriptor_templates['objectDescriptor']

        allowed_pointers = template['pointers'] if 'pointers' in template else []

        for k, v in template.items():
            if k not in ["pointers", "description"] and hasattr(item, k):
                attribute = self.fill_value(k, v, item)
                if k == "ontological_category":
                    k = "type"
                if attribute:
                    returned[k] = attribute
        if hasattr(item, "extras"):
            returned.update(self.get_RDExtras(item.extras))
        for pointer, mods in item.pointers.items():
            if pointer in allowed_pointers:
                for mod in mods:
                    filler = self.fill_pointer(mod, item)
                    if filler:
                        returned.update(filler)
                        if "property" in filler:
                            if self.protagonist is not None:
                                if not "type" in self.protagonist["objectDescriptor"]:
                                    self.protagonist["objectDescriptor"].update(
                                        filler["property"]["objectDescriptor"])

        if 'referent' in returned:
            if returned['referent'] == "antecedent":
                return self.resolve_referents(returned)['objectDescriptor']
            elif item.referent.type() == "anaphora" and not resolving:
                return self.resolve_anaphoricOne(item)['objectDescriptor']
            elif returned['referent'] == "addressee":
                return self.resolve_referents(returned, antecedents=self.addressees)['objectDescriptor']

        return returned

    def compatible_referents(self, pronoun, ref):
        for key, value in pronoun.items():
            if key in ref and key != "referent" and key != "descriptorType" and (value and ref[key]):
                if not self.is_compatible("ONTOLOGY", value, ref[key]):
                    return False
        return True

    def resolve_referents(self, item, antecedents = None, actionary=None, pred=None):
        if antecedents is None:
            antecedents = self._stacked
        popper = list(antecedents)
        while len(popper) > 0:
            ref = popper.pop()
            if self.resolves(ref, actionary, pred) and self.compatible_referents(item, ref['objectDescriptor']):
                ref = self.clean_referent(ref)
                return {'objectDescriptor': self.merge_descriptors(item, ref['objectDescriptor'])}
        return {'objectDescriptor': item}
