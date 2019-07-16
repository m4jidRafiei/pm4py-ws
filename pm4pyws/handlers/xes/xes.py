from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.filtering.log.end_activities import end_activities_filter
from pm4py.algo.filtering.log.start_activities import start_activities_filter
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.objects.conversion.log import factory as conversion_factory
from pm4py.objects.log.exporter.xes.versions.etree_xes_exp import export_log_as_string
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.objects.log.util import insert_classifier
from pm4py.objects.log.util import xes
from pm4py.statistics.traces.log import case_statistics
from pm4py.algo.discovery.dfg import factory as dfg_factory

from pm4py.util import constants
from pm4pyws.util import constants as ws_constants

from pm4pyws.handlers.xes.alignments import get_align
from pm4pyws.handlers.xes.cases import variants
from pm4pyws.handlers.xes.ctmc import transient
from pm4pyws.handlers.xes.filtering import factory as filtering_factory
from pm4pyws.handlers.xes.process_schema import factory as process_schema_factory
from pm4pyws.handlers.xes.sna import get_sna as sna_obtainer
from pm4pyws.handlers.xes.statistics import events_per_time, case_duration, numeric_attribute
from pm4pyws.util import casestats


class XesHandler(object):
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
        self.variants_number = 0
        # number of cases
        self.cases_number = 0
        # number of events
        self.events_number = 0

    def get_filters_chain_repr(self):
        """
        Gets the representation of the current filters chain

        Returns
        -----------
        stri
            Representation of the current filters chain
        """
        return str(self.filters_chain)

    def copy_from_ancestor(self, ancestor):
        """
        Copies from ancestor

        Parameters
        -------------
        ancestor
            Ancestor
        """
        self.first_ancestor = ancestor.first_ancestor
        self.last_ancestor = ancestor
        # self.filters_chain = ancestor.filters_chain
        self.log = ancestor.log
        self.activity_key = ancestor.activity_key

    def remove_filter(self, filter, all_filters):
        """
        Removes a filter from the current handler

        Parameters
        -----------
        filter
            Filter to remove
        all_filters
            All the filters that are still there

        Returns
        ------------
        new_handler
            New handler
        """
        new_handler = XesHandler()
        new_handler.copy_from_ancestor(self.first_ancestor)
        for filter in all_filters:
            new_handler.add_filter0(filter)
        new_handler.build_variants()
        new_handler.calculate_events_number()
        new_handler.calculate_cases_number()
        new_handler.calculate_variants_number()
        return new_handler

    def add_filter(self, filter, all_filters):
        """
        Adds a filter to the current handler

        Parameters
        -----------
        filter
            Filter to add
        all_filters
            All the filters that were added

        Returns
        ------------
        new_handler
            New handler
        """
        new_handler = XesHandler()
        new_handler.copy_from_ancestor(self.first_ancestor)
        for filter in all_filters:
            new_handler.add_filter0(filter)
        new_handler.build_variants()
        new_handler.calculate_events_number()
        new_handler.calculate_cases_number()
        new_handler.calculate_variants_number()
        return new_handler

    def add_filter0(self, filter):
        """
        Technical, void, method to add a filter

        Parameters
        ------------
        filter
            Filter to add
        """
        parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        # parameters["variants"] = self.variants
        self.log = filtering_factory.apply(self.log, filter, parameters=parameters)
        self.filters_chain.append(filter)

    def build_from_path(self, path, parameters=None):
        """
        Builds the handler from the specified path to XES file

        Parameters
        -------------
        path
            Path to the log file
        parameters
            Parameters of the algorithm
        """
        if parameters is None:
            parameters = {}
        try:
            # try faster non standard importer
            self.log = xes_importer.apply(path, variant="nonstandard")
            if len(self.log) == 0:
                # non standard imported failed
                self.log = xes_importer.apply(path)
        except:
            # revert to classic importer
            self.log = xes_importer.apply(path)
        self.log, classifier_key = insert_classifier.search_act_class_attr(self.log,
                                                                           force_activity_transition_insertion=True)

        self.activity_key = xes.DEFAULT_NAME_KEY
        if classifier_key is not None:
            self.activity_key = classifier_key
        self.build_variants()
        self.calculate_variants_number()
        self.calculate_cases_number()
        self.calculate_events_number()

    def build_variants(self, parameters=None):
        """
        Build the variants of the event log

        Parameters
        ------------
        parameters
            Possible parameters of the method
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        self.variants, self.variants_times = variants_filter.get_variants_along_with_case_durations(self.log,
                                                                                                    parameters=parameters)
        self.save_most_common_variant(self.variants)

    def save_most_common_variant(self, variants):
        variants_list = []
        for var in variants:
            var_el = {"variant": var, "count": len(variants[var])}
            variants_list.append(var_el)
        variants_list = sorted(variants_list, key=lambda x: (x["count"], x["variant"]), reverse=True)
        self.most_common_variant = None
        self.most_common_variant = []
        self.most_common_paths = None
        self.most_common_paths = []
        if variants_list:
            best_var_idx = 0
            for i in range(len(variants_list)):
                if len(variants_list[i]["variant"].split(",")) > 1:
                    best_var_idx = i
                    break
            self.most_common_variant = variants_list[best_var_idx]["variant"].split(",")
            for i in range(len(self.most_common_variant)-1):
                self.most_common_paths.append((self.most_common_variant[i], self.most_common_variant[i+1]))

    def calculate_variants_number(self):
        """
        Calculate the number of variants in this log
        """
        self.variants_number = len(self.variants.keys())

    def calculate_cases_number(self):
        """
        Calculate the number of cases in this log
        """
        self.cases_number = len(self.log)

    def calculate_events_number(self):
        """
        Calculate the number of events in this log
        """
        self.events_number = sum([len(case) for case in self.log])

    def get_schema(self, variant=process_schema_factory.DFG_FREQ, parameters=None):
        """
        Gets the process schema in the specified variant and with the specified parameters

        Parameters
        -------------
        variant
            Variant of the algorithm
        parameters
            Parameters of the algorithm

        Returns
        ------------
        schema
            Process schema (in base64)
        model
            Model file possibly describing the process schema
        format
            Format of the process schema (e.g. PNML)
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        parameters[ws_constants.PARAM_MOST_COMMON_VARIANT] = self.most_common_variant
        parameters[ws_constants.PARAM_MOST_COMMON_PATHS] = self.most_common_paths
        return process_schema_factory.apply(self.log, variant=variant, parameters=parameters)

    def get_numeric_attribute_svg(self, attribute, parameters=None):
        """
        Get the SVG of a numeric attribute

        Parameters
        ------------
        attribute
            Attribute
        parameters
            Other possible parameters
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key

        return numeric_attribute.get_numeric_attribute_distr_svg(self.log, attribute, parameters=parameters)

    def get_case_duration_svg(self, parameters=None):
        """
        Gets the SVG of the case duration

        Parameters
        ------------
        parameters
            Parameters of the algorithm

        Returns
        -----------
        graph
            Case duration graph (expressed in Base 64)
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        return case_duration.get_case_duration_svg(self.log, parameters=parameters)

    def get_events_per_time_svg(self, parameters=None):
        """
        Gets the SVG of the events per time

        Parameters
        -------------
        parameters
            Parameters of the algorithm

        Returns
        -------------
        graph
            Events per time graph (expressed in Base 64)
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        return events_per_time.get_events_per_time_svg(self.log, parameters=parameters)

    def get_variant_statistics(self, parameters=None):
        """
        Gets the variants of the given log

        Parameters
        --------------
        parameters
            Parameters of the algorithm

        Returns
        --------------
        variants
            Variants of the log
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        parameters["variants"] = self.variants
        parameters["var_durations"] = self.variants_times
        return variants.get_statistics(self.log, parameters=parameters)

    def get_sna(self, variant="handover", parameters=None):
        """
        Gets a Social Network representation from a given log

        Parameters
        -------------
        variant
            Variant of the algorithm (metric to use)
        parameters
            Parameters of the algorithm (e.g. arc threshold)

        Returns
        ------------
        sna
            SNA representation
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        return sna_obtainer.apply(self.log, variant=variant, parameters=parameters)

    def get_transient(self, delay, parameters=None):
        """
        Perform CTMC simulation on a log

        Parameters
        -------------
        delay
            Delay
        parameters
            Possible parameters of the algorithm

        Returns
        -------------
        graph
            Case duration graph
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        return transient.apply(self.log, delay, parameters=parameters)

    def get_case_statistics(self, parameters=None):
        """
        Gets the statistics on cases

        Parameters
        -------------
        parameters
            Possible parameters of the algorithm

        Returns
        -------------
        list_cases
            List of cases
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        parameters["max_ret_cases"] = 500
        parameters["sort_by_index"] = parameters["sort_by_index"] if "sort_by_index" in parameters else 0
        parameters["sort_ascending"] = parameters["sort_ascending"] if "sort_ascending" in parameters else False
        parameters["variants"] = self.variants
        if "variant" in parameters:
            var_to_filter = parameters["variant"]
            # TODO: TECHNICAL DEBT
            # quick turnaround for bug
            var_to_filter = var_to_filter.replace(" start", "+start")
            var_to_filter = var_to_filter.replace(" START", "+START")
            var_to_filter = var_to_filter.replace(" complete", "+complete")
            var_to_filter = var_to_filter.replace(" COMPLETE", "+COMPLETE")
            filtered_log = variants_filter.apply(self.log, [var_to_filter], parameters=parameters)
            return casestats.include_key_in_value_list(
                case_statistics.get_cases_description(filtered_log, parameters=parameters))
        else:
            return casestats.include_key_in_value_list(
                case_statistics.get_cases_description(self.log, parameters=parameters))

    def get_events(self, caseid, parameters=None):
        """
        Gets the events of a case

        Parameters
        -------------
        caseid
            Case ID
        parameters
            Parameters of the algorithm

        Returns
        ------------
        list_events
            Events belonging to the case
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        return case_statistics.get_events(self.log, caseid, parameters=parameters)

    def get_alignments(self, petri_string, parameters=None):
        """
        Gets the alignments from a string

        Parameters
        -------------
        petri_string
            Petri string
        parameters
            Parameters of the algorithm

        Returns
        -------------
        petri
            SVG of the decorated Petri
        table
            SVG of the decorated table
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        return get_align.perform_alignments(self.log, petri_string, parameters=parameters)

    def download_xes_log(self):
        """
        Downloads the XES log as string
        """
        log_string = export_log_as_string(self.log)
        return log_string

    def download_csv_log(self):
        """
        Downloads the CSV log as string
        """
        dataframe = conversion_factory.apply(self.log, variant=conversion_factory.TO_DATAFRAME)
        log_string = dataframe.to_string()
        return log_string

    def get_start_activities(self, parameters=None):
        """
        Gets the start activities from the log

        Returns
        ------------
        start_activities_dict
            Dictionary of start activities
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        return start_activities_filter.get_start_activities(self.log, parameters=parameters)

    def get_end_activities(self, parameters=None):
        """
        Gets the end activities from the log

        Returns
        -------------
        end_activities_dict
            Dictionary of end activities
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        return end_activities_filter.get_end_activities(self.log, parameters=parameters)

    def get_attributes_list(self, parameters=None):
        """
        Gets the attributes list from the log

        Returns
        -------------
        attributes_list
            List of attributes
        """
        return attributes_filter.get_all_event_attributes_from_log(self.log)

    def get_attribute_values(self, attribute_key, parameters=None):
        """
        Gets the attribute values from the log

        Returns
        -------------
        attribute_values
            List of values
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = attribute_key
        initial_dict = attributes_filter.get_attribute_values(self.log, attribute_key, parameters=parameters)
        return_dict = {}
        for key in initial_dict:
            return_dict[str(key)] = int(initial_dict[key])
        return return_dict

    def get_paths(self, attribute_key, parameters=None):
        """
        Gets the paths from the log

        Parameters
        -------------
        attribute_key
            Attribute key

        Returns
        -------------
        paths
            List of paths
        """
        dfg = dfg_factory.apply(self.log, parameters={constants.PARAMETER_CONSTANT_ACTIVITY_KEY: attribute_key})

        return dfg
