from p_connector_dfg.privacyPreserving import privacyPreserving

class XmlHandler(object):
    def __init__(self):
        """
        Constructor (set all variables to None)
        """

        # sets the current log to None
        self.log = None
        # sets the first ancestor (in the filtering chain) to None
        self.first_ancestor = self
        # sets the last ancestor (in the filtering chain) to None
        self.last_ancestor = self
        # sets the filter chain
        self.filters_chain = []
        # classifier
        self.activity_key = None
        # variants
        self.variants = None
        # most common variant (activities)
        self.most_common_variant = None
        # most common variant (paths)
        self.most_common_paths = None
        # number of variants
        self.variants_number = -1
        # number of cases
        self.cases_number = -1
        # number of events
        self.events_number = -1
        # events map (correspondency)
        self.event_map = None

    def get_filters_chain_repr(self):
        raise Exception("not implemented error")

    def copy_from_ancestor(self, ancestor):
        raise Exception("not implemented error")

    def remove_filter(self, filter, all_filters):
        raise Exception("not implemented error")

    def add_filter(self, filter, all_filters):
        raise Exception("not implemented error")

    def add_filter0(self, filter):
        raise Exception("not implemented error")

    def build_from_path(self, path, parameters=None):
        raise Exception("not implemented error")

    def insert_event_index(self):
        raise Exception("not implemented error")

    def build_variants(self, parameters=None):
        raise Exception("not implemented error")

    def save_most_common_variant(self, variants):
        raise Exception("not implemented error")

    def calculate_variants_number(self):
        raise Exception("not implemented error")

    def calculate_cases_number(self):
        raise Exception("not implemented error")

    def calculate_events_number(self):
        raise Exception("not implemented error")

    def get_variants_number(self):
        raise Exception("not implemented error")

    def get_cases_number(self):
        raise Exception("not implemented error")

    def get_events_number(self):
        raise Exception("not implemented error")

    def get_schema(self, arameters=None):
        raise Exception("not implemented error")

    def get_numeric_attribute_svg(self, attribute, parameters=None):
        raise Exception("not implemented error")

    def get_case_duration_svg(self, parameters=None):
        raise Exception("not implemented error")

    def get_events_per_time_svg(self, parameters=None):
        raise Exception("not implemented error")

    def get_variant_statistics(self, parameters=None):
        raise Exception("not implemented error")

    def get_sna(self, variant="handover", parameters=None):
        raise Exception("not implemented error")

    def get_transient(self, delay, parameters=None):
        raise Exception("not implemented error")

    def get_case_statistics(self, parameters=None):
        raise Exception("not implemented error")

    def get_events(self, caseid, parameters=None):
        raise Exception("not implemented error")

    def get_alignments(self, petri_string, parameters=None):
        raise Exception("not implemented error")

    def download_xes_log(self):
        raise Exception("not implemented error")

    def download_csv_log(self):
        raise Exception("not implemented error")

    def get_start_activities(self, parameters=None):
        raise Exception("not implemented error")

    def get_end_activities(self, parameters=None):
        raise Exception("not implemented error")

    def get_attributes_list(self, parameters=None):
        return attributes_filter.get_all_event_attributes_from_log(self.log)

    def get_attribute_values(self, attribute_key, parameters=None):
        raise Exception("not implemented error")

    def get_paths(self, attribute_key, parameters=None):
        raise Exception("not implemented error")

    def get_trace_attributes(self):
        raise Exception("not implemented error")

    def get_events_for_dotted(self, attributes):
        raise Exception("not implemented error")

    def get_spec_event_by_idx(self, ev_idx):
        raise Exception("not implemented error")

    def get_log_summary_dictio(self):
        raise Exception("not implemented error")

    def get_content(self, log_path):
        pp = privacyPreserving(None)
        pp.result_maker_pma(pma_path, True,True, True, 0.0)

        raise Exception("not implemented error")

