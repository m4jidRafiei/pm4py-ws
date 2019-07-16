from pm4py.algo.discovery.inductive.versions.dfg import imdfb as inductive_miner
from pm4py.objects.petri.exporter.pnml import export_petri_as_string
from pm4py.visualization.common.utils import get_base64_from_gviz, get_base64_from_file
from pm4py.visualization.petrinet import factory as pn_vis_factory
from pm4py.algo.filtering.log.auto_filter import auto_filter
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.conformance.tokenreplay.versions import token_replay
from pm4py.util import constants as pm4_constants
from pm4py.objects.log.util import xes
from pm4py.algo.filtering.log.start_activities import start_activities_filter
from pm4py.algo.filtering.log.end_activities import end_activities_filter
from pm4pyws.util import get_graph
from pm4py.visualization.petrinet.versions import token_decoration
from pm4pybpmn.visualization.bpmn.util import convert_performance_map
from pm4pybpmn.objects.bpmn.exporter import bpmn20 as bpmn_exporter
import base64

from pm4pyws.util import constants

from pm4pybpmn.objects.conversion.petri_to_bpmn import factory as petri_to_bpmn
from pm4pybpmn.visualization.bpmn import factory as bpmn_vis_factory
from pm4pybpmn.visualization.bpmn.util import bpmn_embedding
from pm4pybpmn.objects.bpmn.util import bpmn_diagram_layouter
from pm4pybpmn.visualization.bpmn.util import convert_performance_map

from pm4py.algo.filtering.dfg.dfg_filtering import clean_dfg_based_on_noise_thresh
from pm4py.algo.discovery.dfg import factory as dfg_factory


def apply(log, parameters=None):
    """
    Gets the Petri net through Inductive Miner, decorated by frequency metric

    Parameters
    ------------
    log
        Log
    parameters
        Parameters of the algorithm

    Returns
    ------------
    base64
        Base64 of an SVG representing the model
    model
        Text representation of the model
    format
        Format of the model
    """
    if parameters is None:
        parameters = {}

    decreasingFactor = parameters[
        "decreasingFactor"] if "decreasingFactor" in parameters else constants.DEFAULT_DEC_FACTOR

    activity_key = parameters[
        pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY] if pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY in parameters else xes.DEFAULT_NAME_KEY

    # reduce the depth of the search done by token-based replay
    token_replay.MAX_REC_DEPTH = 1
    token_replay.MAX_IT_FINAL1 = 1
    token_replay.MAX_IT_FINAL2 = 1
    token_replay.MAX_REC_DEPTH_HIDTRANSENABL = 1

    log = attributes_filter.filter_log_on_max_no_activities(log, max_no_activities=constants.MAX_NO_ACTIVITIES,
                                                            parameters=parameters)
    filtered_log = auto_filter.apply_auto_filter(log, parameters=parameters)

    activities_count = attributes_filter.get_attribute_values(filtered_log, activity_key)
    activities = list(activities_count.keys())
    start_activities = list(start_activities_filter.get_start_activities(filtered_log, parameters=parameters).keys())
    end_activities = list(end_activities_filter.get_end_activities(filtered_log, parameters=parameters).keys())

    dfg = dfg_factory.apply(filtered_log, parameters=parameters)
    dfg = clean_dfg_based_on_noise_thresh(dfg, activities, decreasingFactor * constants.DEFAULT_DFG_CLEAN_MULTIPLIER,
                                          parameters=parameters)
    net, im, fm = inductive_miner.apply_dfg(dfg, parameters=parameters, activities=activities,
                                            start_activities=start_activities, end_activities=end_activities)
    # parameters["format"] = "svg"
    # gviz = pn_vis_factory.apply(net, im, fm, log=log, variant="frequency", parameters=parameters)

    bpmn_graph, el_corr, inv_el_corr, el_corr_keys_map = petri_to_bpmn.apply(net, im, fm)

    aggregated_statistics = token_decoration.get_decorations(filtered_log, net, im, fm,
                                                             parameters=parameters, measure="frequency")

    bpmn_aggreg_statistics = convert_performance_map.convert_performance_map_to_bpmn(aggregated_statistics,
                                                                                     inv_el_corr)
    # bpmn_graph = bpmn_embedding.embed_info_into_bpmn(bpmn_graph, bpmn_aggreg_statistics, "frequency")
    bpmn_graph = bpmn_diagram_layouter.apply(bpmn_graph)
    bpmn_string = bpmn_exporter.get_string_from_bpmn(bpmn_graph)

    gviz = bpmn_vis_factory.apply_petri(net, im, fm, aggregated_statistics=aggregated_statistics, variant="frequency",
                                        parameters={"format": "svg"})
    gviz2 = bpmn_vis_factory.apply_petri(net, im, fm, aggregated_statistics=aggregated_statistics, variant="frequency",
                                         parameters={"format": "dot"})

    svg = get_base64_from_file(gviz.name)

    gviz_base64 = get_base64_from_file(gviz2.name)

    ret_graph = get_graph.get_graph_from_petri(net, im, fm)

    return svg, export_petri_as_string(net, im,
                                       fm), ".pnml", "xes", activities, start_activities, end_activities, gviz_base64, ret_graph, "indbpmn", "freq", bpmn_string, ".bpmn", activity_key
