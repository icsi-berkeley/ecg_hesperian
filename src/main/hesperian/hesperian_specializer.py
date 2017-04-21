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

    def specialize_fragment(self, fs):
        if not hasattr(fs, "m") or fs.m == "None":
            return None
        elif self.analyzer.issubtype("SCHEMA", fs.m.type(), "Symptom"):
            return self.fill_parameters(fs.m)
        else:
            return CoreSpecializer.specialize_fragment(self, fs)
