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

    # def specialize_fragment(self, fs):
    #     if not hasattr(fs, "m") or fs.m == "None":
    #         return None
    #     elif self.analyzer.issubtype("SCHEMA", fs.m.type(), "Symptom"):
    #         return self.fill_parameters(fs.m)
    #     else:
    #         return CoreSpecializer.specialize_fragment(self, fs)

    # def get_objectDescriptor(self, item, resolving=False):
    #     """ Override to use correct descriptors for symptoms, diseases and drugs """
    #     if "pointers" not in item.__dir__():
    #         item.pointers = self.invert_pointers(item)
    #
    #     if self.analyzer.issubtype("SCHEMA", item.type(), "Symptom"):
    #         return self.get_symptomDescriptor(item, resolving)
    #     elif self.analyzer.issubtype("SCHEMA", item.type(), "Disease"):
    #         return self.get_diseaseDescriptor(item, resolving)
    #     elif self.analyzer.issubtype("SCHEMA", item.type(), "Drug"):
    #         return self.get_treatmentDescriptor(item, resolving)
    #     else:
    #         return CoreSpecializer.get_objectDescriptor(item, resolving)

    def get_symptomDescriptor(self, item, resolving=False):
        return self.get_objectDescriptor(item, resolving)

    def get_diseaseDescriptor(self, item, resolving=False):
        return self.get_objectDescriptor(item, resolving)

    def get_treatmentDescriptor(self, item, resolving=False):
        return self.get_objectDescriptor(item, resolving)

    def get_patientDescriptor(self, item, resolving=False):
        return self.get_objectDescriptor(item, resolving)

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


    def fill_value(self, key, value, input_schema):
        """ Most important specializer method. Takes in a skeleton key,value pairing from a template,
        as well as the relevant schema ("MotionPath", etc.), and returns the relevant value.
        If the value is a dictionary, it might be a "descriptor", so it returns an objectDescriptor, etc.
        A dictionary value could also indicate an embedded process, in which case fill_parameters is called.
        Also calls specialize_event for embedded EventDescriptors.
        Otherwise, it gets the filler for the value from the schema ("actionary": @move), and returns this.
        """
        final_value = None
        if isinstance(value, dict):
            if "method" in value and hasattr(input_schema, key):
                method = getattr(self, value["method"])
                return method(input_schema)
            elif "descriptor" in value:
                method = getattr(self, "get_{}".format(value["descriptor"]))
                if hasattr(input_schema, key) and getattr(input_schema, key).has_filler():
                    attribute = getattr(input_schema, key)
                    descriptor = {value['descriptor']: method(attribute)}
                    if value['descriptor'] in ["objectDescriptor", "symptomDescriptor", "diseaseDescriptor", "treatmentDescriptor", "patientDescriptor"]:
                        self._stacked.append(descriptor)
                    if key == "protagonist":
                        self.protagonist = dict(descriptor)
                    return descriptor
                if "default" in value:
                    return value['default']
                return None
            elif "parameters" in value and hasattr(input_schema, value['parameters']) and getattr(input_schema, value['parameters']).has_filler():
                return self.fill_parameters(getattr(input_schema, value['parameters']))
            elif "eventDescription" in value and hasattr(input_schema, value['eventDescription']) and getattr(input_schema, value['eventDescription']).has_filler():
                return self.specialize_event(getattr(input_schema, value['eventDescription']))
        elif value and hasattr(input_schema, key):
            attribute = getattr(input_schema, key)
            if attribute.type() in ["scalarValue", "scale"]:
                return float(attribute)
            elif key == "negated":
                return self.get_negated(attribute.type())
            elif attribute.type() != "None" and attribute.type() != None:
                return attribute.type()
            elif attribute.__value__ != "None":
                return attribute.__value__

        return final_value
