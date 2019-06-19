from pm4py.algo.filtering.common.filtering_constants import CASE_CONCEPT_NAME
from pm4py.algo.filtering.pandas.attributes import attributes_filter
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from pm4py.algo.filtering.pandas.start_activities import start_activities_filter
from pm4py.algo.filtering.pandas.variants import variants_filter
from pm4py.objects.conversion.log import factory as conv_factory
from pm4py.objects.log.adapters.pandas import csv_import_adapter
from pm4py.objects.log.exporter.xes.versions import etree_xes_exp
from pm4py.objects.log.importer.parquet import factory as parquet_importer
from pm4py.objects.log.util import xes
from pm4py.statistics.traces.pandas import case_statistics
from pm4py.util import constants

from pm4pyws.handlers.parquet.cases import variants
from pm4pyws.handlers.parquet.ctmc import transient
from pm4pyws.handlers.parquet.process_schema import factory as process_schema_factory
from pm4pyws.handlers.parquet.sna import get_sna as sna_obtainer
from pm4pyws.handlers.parquet.statistics import case_duration, events_per_time, numeric_attribute
from pm4pyws.util import casestats
from pm4pyws.handlers.parquet.filtering import factory as filtering_factory
from pm4pyws.handlers.parquet.alignments import get_align

import pandas as pd


class ParquetHandler(object):
    def __init__(self):
        """
        Constructor (set all variables to None)
        """

        # sets the current dataframe to None
        self.dataframe = None
        # grouped dataframe
        self.grouped_dataframe = None
        # sets the first ancestor (in the filtering chain) to None
        self.first_ancestor = self
        # sets the last ancestor (in the filtering chain) to None
        self.last_ancestor = self
        # sets the filter chain
        self.filters_chain = []
        # sets the variant dataframe (useful in variants retrieval)
        self.variants_df = None
        # number of variants
        self.variants_number = 0
        # number of cases
        self.cases_number = 0
        # number of events
        self.events_number = 0
        # classifier
        self.activity_key = None

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
        self.activity_key = ancestor.activity_key
        # self.filters_chain = ancestor.filters_chain
        self.dataframe = ancestor.dataframe
        self.grouped_dataframe = ancestor.grouped_dataframe

    def build_from_path(self, path, parameters=None):
        """
        Builds the handler from the specified path to Parquet file

        Parameters
        -------------
        path
            Path to the log file
        parameters
            Parameters of the algorithm
        """
        if parameters is None:
            parameters = {}
        self.dataframe = parquet_importer.apply(path)
        # TODO: verify if this is the best way to act
        self.dataframe["time:timestamp"] = pd.to_datetime(self.dataframe["time:timestamp"], utc=True)
        self.postloading_processing_dataframe()
        self.build_variants_df()
        self.grouped_dataframe = self.dataframe.groupby(CASE_CONCEPT_NAME)
        self.calculate_events_number()
        self.calculate_variants_number()
        self.calculate_cases_number()

    def build_from_csv(self, path, parameters=None):
        """
        Builds the handler from the specified path to CSV file

        Parameters
        -------------
        path
            Path to the log file
        parameters
            Parameters of the algorithm
        """
        if parameters is None:
            parameters = {}
        activity_key = parameters[
            constants.PARAMETER_CONSTANT_ACTIVITY_KEY] if constants.PARAMETER_CONSTANT_ACTIVITY_KEY in parameters else xes.DEFAULT_NAME_KEY
        timestamp_key = parameters[
            constants.PARAMETER_CONSTANT_TIMESTAMP_KEY] if constants.PARAMETER_CONSTANT_TIMESTAMP_KEY in parameters else xes.DEFAULT_TIMESTAMP_KEY
        case_id_glue = parameters[
            constants.PARAMETER_CONSTANT_CASEID_KEY] if constants.PARAMETER_CONSTANT_CASEID_KEY in parameters else CASE_CONCEPT_NAME
        sep = parameters["sep"] if "sep" in parameters else ","
        quotechar = parameters["quotechar"] if "quotechar" in parameters else None

        if quotechar is not None:
            self.dataframe = csv_import_adapter.import_dataframe_from_path(path, sep=sep, quotechar=quotechar)
        else:
            self.dataframe = csv_import_adapter.import_dataframe_from_path(path, sep=sep)

        if not activity_key == xes.DEFAULT_NAME_KEY:
            self.dataframe[xes.DEFAULT_NAME_KEY] = activity_key
        if not timestamp_key == xes.DEFAULT_TIMESTAMP_KEY:
            self.dataframe[xes.DEFAULT_TIMESTAMP_KEY] = timestamp_key
        if not case_id_glue == CASE_CONCEPT_NAME:
            self.dataframe[case_id_glue] = CASE_CONCEPT_NAME
        self.postloading_processing_dataframe()
        self.build_variants_df()
        self.grouped_dataframe = self.dataframe.groupby(CASE_CONCEPT_NAME)
        self.calculate_variants_number()
        self.calculate_cases_number()
        self.calculate_events_number()

    def postloading_processing_dataframe(self):
        """
        Postloading processing of the dataframe
        """

        self.dataframe[xes.DEFAULT_NAME_KEY] = self.dataframe[xes.DEFAULT_NAME_KEY].astype(str)
        if xes.DEFAULT_TRANSITION_KEY in self.dataframe:
            self.dataframe[xes.DEFAULT_TRANSITION_KEY] = self.dataframe[xes.DEFAULT_TRANSITION_KEY].astype(str)
            self.dataframe["@@classifier"] = self.dataframe[xes.DEFAULT_NAME_KEY] + "+" + self.dataframe[
                xes.DEFAULT_TRANSITION_KEY]
        else:
            self.dataframe["@@classifier"] = self.dataframe[xes.DEFAULT_NAME_KEY]
        self.activity_key = "@@classifier"

        if xes.DEFAULT_TIMESTAMP_KEY in self.dataframe:
            self.dataframe = self.dataframe.sort_values([CASE_CONCEPT_NAME, xes.DEFAULT_TIMESTAMP_KEY])
        else:
            self.dataframe = self.dataframe.sort_values(CASE_CONCEPT_NAME)

        #self.dataframe["@@index"] = self.dataframe.index

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
        new_handler = ParquetHandler()
        new_handler.copy_from_ancestor(self.first_ancestor)
        for filter in all_filters:
            new_handler.add_filter0(filter)
        new_handler.build_variants_df()
        new_handler.grouped_dataframe = new_handler.dataframe.groupby(CASE_CONCEPT_NAME)
        new_handler.calculate_cases_number()
        new_handler.calculate_variants_number()
        new_handler.calculate_events_number()
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
        new_handler = ParquetHandler()
        new_handler.copy_from_ancestor(self.first_ancestor)
        for filter in all_filters:
            new_handler.add_filter0(filter)
        new_handler.build_variants_df()
        new_handler.grouped_dataframe = new_handler.dataframe.groupby(CASE_CONCEPT_NAME)
        new_handler.calculate_cases_number()
        new_handler.calculate_variants_number()
        new_handler.calculate_events_number()
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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe
        # parameters["variants_df"] = self.variants_df
        self.dataframe = filtering_factory.apply(self.dataframe, filter, parameters=parameters)
        self.filters_chain.append(filter)

    def build_variants_df(self, parameters=None):
        """
        Builds the variants dataframe

        Parameters
        --------------
        parameters
            Possible parameters of the algorithm
        """
        if parameters is None:
            parameters = {}
        parameters[constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = self.activity_key
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        self.variants_df = case_statistics.get_variants_df_with_case_duration(self.dataframe, parameters=parameters)

    def calculate_variants_number(self):
        """
        Calculate the number of variants in this log
        """
        self.variants_number = len(self.variants_df.groupby("variant"))

    def calculate_cases_number(self):
        """
        Calculate the number of cases in this log
        """
        self.cases_number = len(self.grouped_dataframe)

    def calculate_events_number(self):
        """
        Calculate the number of events in this log
        """
        self.events_number = len(self.dataframe)

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        parameters["variants_df"] = self.variants_df
        return process_schema_factory.apply(self.dataframe, variant=variant, parameters=parameters)

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        return numeric_attribute.get_numeric_attribute_distr_svg(self.dataframe, attribute, parameters=parameters)

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        return case_duration.get_case_duration_svg(self.dataframe, parameters=parameters)

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        return events_per_time.get_events_per_time_svg(self.dataframe, parameters=parameters)

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        parameters["variants_df"] = self.variants_df

        return variants.get_statistics(self.dataframe, parameters=parameters)

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        return sna_obtainer.apply(self.dataframe, variant=variant, parameters=parameters)

    def get_transient(self, delay, parameters=None):
        """
        Perform CTMC simulation on a dataframe

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        return transient.apply(self.dataframe, delay, parameters=parameters)

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe
        parameters["max_ret_cases"] = 500
        parameters["sort_by_column"] = parameters[
            "sort_by_column"] if "sort_by_column" in parameters else "caseDuration"
        parameters["sort_ascending"] = parameters["sort_ascending"] if "sort_ascending" in parameters else False

        if "variant" in parameters:
            var_to_filter = parameters["variant"]
            # TODO: TECHNICAL DEBT
            # quick turnaround for bug
            var_to_filter = var_to_filter.replace(" start","+start")
            var_to_filter = var_to_filter.replace(" START", "+START")
            var_to_filter = var_to_filter.replace(" complete", "+complete")
            var_to_filter = var_to_filter.replace(" COMPLETE", "+COMPLETE")

            filtered_dataframe = variants_filter.apply(self.dataframe, [var_to_filter], parameters=parameters)
            return casestats.include_key_in_value_list(
                case_statistics.get_cases_description(filtered_dataframe, parameters=parameters))
        else:
            return casestats.include_key_in_value_list(
                case_statistics.get_cases_description(self.dataframe, parameters=parameters))

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe
        return case_statistics.get_events(self.dataframe, caseid, parameters=parameters)

    def download_xes_log(self):
        """
        Downloads the XES log as string
        """
        return etree_xes_exp.export_log_as_string(conv_factory.apply(self.dataframe))

    def download_csv_log(self):
        """
        Downloads the CSV log as string
        """
        return self.dataframe.to_string()

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        return start_activities_filter.get_start_activities(self.dataframe, parameters=parameters)

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        return end_activities_filter.get_end_activities(self.dataframe, parameters=parameters)

    def get_attributes_list(self, parameters=None):
        """
        Gets the attributes list from the log

        Returns
        -------------
        attributes_list
            List of attributes
        """
        return list(self.dataframe.columns)

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
        parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = self.activity_key
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        initial_dict = attributes_filter.get_attribute_values(self.dataframe, attribute_key, parameters=parameters)
        return_dict = {}
        for key in initial_dict:
            return_dict[str(key)] = int(initial_dict[key])
        return return_dict

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
        parameters[constants.GROUPED_DATAFRAME] = self.grouped_dataframe

        return get_align.perform_alignments(self.dataframe, petri_string, parameters=parameters)
