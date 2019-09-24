from pm4py.objects.log.util import xes
from pm4pyws.handlers.distributed.process_schema import factory as process_schema_factory
from pm4pyws.handlers.distributed.statistics import case_duration, events_per_time, numeric_attribute
from pm4py.util import constants
from copy import deepcopy


class DistributedHandler(object):
    def __init__(self, wrapper, parameters=None):
        if parameters is None:
            parameters = {}
        self.wrapper = wrapper
        # sets the filter chain
        self.filters_chain = []
        # classifier
        self.activity_key = xes.DEFAULT_NAME_KEY

        self.first_ancestor = self

    def get_filters_chain_repr(self):
        """
        Gets the representation of the current filters chain

        Returns
        -----------
        stri
            Representation of the current filters chain
        """
        return str(self.filters_chain)

    def remove_filter(self, filter, all_filters):
        self.wrapper.set_filters(all_filters)
        return self

    def add_filter(self, filter, all_filters):
        self.wrapper.set_filters(all_filters)
        return self

    def get_variants_number(self):
        # the number is not implemented
        return -1

    def get_cases_number(self):
        summary = self.wrapper.get_log_summary()
        return summary["cases"]

    def get_events_number(self):
        summary = self.wrapper.get_log_summary()
        return summary["events"]

    def get_schema(self, variant=process_schema_factory.DFG_FREQ, parameters=None):
        return process_schema_factory.apply(self.wrapper, variant=variant, parameters=parameters)

    def get_numeric_attribute_svg(self, attribute, parameters=None):
        return numeric_attribute.get_numeric_attribute_distr_svg(self.wrapper, attribute, parameters=parameters)

    def get_case_duration_svg(self, parameters=None):
        return case_duration.get_case_duration_svg(self.wrapper, parameters=parameters)

    def get_events_per_time_svg(self, parameters=None):
        return events_per_time.get_events_per_time_svg(self.wrapper, parameters=parameters)

    def get_variant_statistics(self, parameters=None):
        dictio = self.wrapper.get_variants()

        return [dictio["variants"], {"this_events_number": dictio["events"], "this_cases_number": dictio["cases"], "this_variants_number": -1, "ancestor_events_number": dictio["events"], "ancestor_cases_number": dictio["cases"], "ancestor_variants_number": -1}]

    def get_sna(self, variant="handover", parameters=None):
        pass

    def get_transient(self, delay, parameters=None):
        pass

    def get_case_statistics(self, parameters=None):
        if parameters is None:
            parameters = {}

        if "variant" in parameters:
            var_to_filter = parameters["variant"]
            # TODO: TECHNICAL DEBT
            # quick turnaround for bug
            var_to_filter = var_to_filter.replace(" start", "+start")
            var_to_filter = var_to_filter.replace(" START", "+START")
            var_to_filter = var_to_filter.replace(" complete", "+complete")
            var_to_filter = var_to_filter.replace(" COMPLETE", "+COMPLETE")

            old_filters = deepcopy(self.wrapper.filters)
            self.wrapper.set_filters(old_filters + [["variants", [var_to_filter]]])
            dictio = self.wrapper.get_cases()
            self.wrapper.set_filters(old_filters)
        else:
            dictio = self.wrapper.get_cases()

        return [dictio["cases_list"], {"this_events_number": dictio["events"], "this_cases_number": dictio["cases"], "this_variants_number": -1, "ancestor_events_number": dictio["events"], "ancestor_cases_number": dictio["cases"], "ancestor_variants_number": -1}]

    def get_events(self, caseid, parameters=None):
        return self.wrapper.get_events(caseid)

    def download_xes_log(self):
        pass

    def download_csv_log(self):
        pass

    def get_start_activities(self, parameters=None):
        return self.wrapper.get_start_activities()

    def get_end_activities(self, parameters=None):
        return self.wrapper.get_end_activities()

    def get_attributes_list(self, parameters=None):
        return self.wrapper.get_attribute_names()

    def get_attribute_values(self, attribute_key, parameters=None):
        return self.wrapper.get_attribute_values(attribute_key)

    def get_paths(self, attribute_key, parameters=None):
        return self.wrapper.calculate_dfg(parameters={constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY: attribute_key})

    def get_alignments(self, petri_string, parameters=None):
        pass

    def get_events_for_dotted(self, attributes):
        if len(attributes) > 2:
            dictio = self.wrapper.get_events_per_dotted(attributes[0], attributes[1], attributes[2])
        else:
            dictio = self.wrapper.get_events_per_dotted(attributes[0], attributes[1])

        return dictio["traces"], dictio["types"], dictio["attributes"], dictio["third_unique_values"]

    def get_spec_event_by_idx(self, ev_idx):
        pass

    def get_log_summary_dictio(self):
        summary = self.wrapper.get_log_summary()
        this_variants_number = -1
        this_cases_number = summary["cases"]
        this_events_number = summary["events"]
        ancestor_variants_number = -1
        ancestor_cases_number = summary["cases"]
        ancestor_events_number = summary["events"]

        dictio = {"this_variants_number": this_variants_number, "this_cases_number": this_cases_number,
                  "this_events_number": this_events_number, "ancestor_variants_number": ancestor_variants_number,
                  "ancestor_cases_number": ancestor_cases_number, "ancestor_events_number": ancestor_events_number}

        return dictio
