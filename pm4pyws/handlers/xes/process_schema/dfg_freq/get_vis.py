from pm4py.algo.discovery.dfg import factory as dfg_factory
from pm4py.visualization.dfg import factory as dfg_vis_factory
from pm4py.visualization.common.utils import get_base64_from_gviz
from pm4py.algo.filtering.log.auto_filter import auto_filter
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.util import constants as pm4_constants
from pm4py.objects.log.util import xes
from pm4py.algo.filtering.log.start_activities import start_activities_filter
from pm4py.algo.filtering.log.end_activities import end_activities_filter
from pm4py.objects.conversion.dfg import factory as dfg_conv_factory
from pm4py.objects.petri.exporter.pnml import export_petri_as_string
from pm4pyws.util import get_graph
import base64

from pm4pyws.util import constants

from pm4py.algo.filtering.dfg.dfg_filtering import clean_dfg_based_on_noise_thresh


def apply(log, parameters=None):
    """
    Gets the frequency DFG

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

    parameters["format"] = "svg"
    parameters["start_activities"] = start_activities
    parameters["end_activities"] = end_activities

    gviz = dfg_vis_factory.apply(dfg, log=filtered_log, variant="frequency", parameters=parameters)

    gviz_base64 = base64.b64encode(str(gviz).encode('utf-8'))

    ret_graph = get_graph.get_graph_from_dfg(dfg, start_activities, end_activities)

    net, im, fm = dfg_conv_factory.apply(dfg, parameters={"start_activities": start_activities,
                                                          "end_activities": end_activities})

    return get_base64_from_gviz(gviz), export_petri_as_string(net, im,
                                                              fm), ".pnml", "xes", activities, start_activities, end_activities, gviz_base64, ret_graph, "dfg", "freq", None, "", activity_key
