from pm4py.objects.log.util import xes
from pm4pyws.handlers.distributed.process_schema import factory as process_schema_factory

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
        raise Exception("not implemented")

    def add_filter(self, filter, all_filters):
        raise Exception("not implemented")

    def get_variants_number(self):
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
        pass

    def get_case_duration_svg(self, parameters=None):
        pass

    def get_events_per_time_svg(self, parameters=None):
        pass

    def get_variant_statistics(self, parameters=None):
        pass

    def get_sna(self, variant="handover", parameters=None):
        pass

    def get_transient(self, delay, parameters=None):
        pass

    def get_case_statistics(self, parameters=None):
        pass

    def get_events(self, caseid, parameters=None):
        pass

    def download_xes_log(self):
        pass

    def download_csv_log(self):
        pass

    def get_start_activities(self, parameters=None):
        pass

    def get_end_activities(self, parameters=None):
        pass

    def get_attributes_list(self, parameters=None):
        pass

    def get_attribute_values(self, attribute_key, parameters=None):
        pass

    def get_paths(self, attribute_key, parameters=None):
        pass

    def get_alignments(self, petri_string, parameters=None):
        pass

    def get_events_for_dotted(self, attributes):
        pass

    def get_spec_event_by_idx(self, ev_idx):
        pass
