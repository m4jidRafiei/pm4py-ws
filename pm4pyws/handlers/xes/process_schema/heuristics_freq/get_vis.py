from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.filtering.log.auto_filter import auto_filter
from pm4py.objects.heuristics_net.net import HeuristicsNet
from pm4py.visualization.common.utils import get_base64_from_file
from pm4py.visualization.heuristics_net import factory as heu_vis_factory
from pm4py.algo.discovery.dfg import factory as dfg_factory
from pm4py.util import constants as pm4_constants
from pm4py.objects.log.util import xes
from pm4py.algo.filtering.log.start_activities import start_activities_filter
from pm4py.algo.filtering.log.end_activities import end_activities_filter
import base64

from pm4pyws.util import constants


def apply(log, parameters=None):
    """
    Gets the frequency HNet

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

    activity_key = parameters[pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY] if pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY in parameters else xes.DEFAULT_NAME_KEY

    log = attributes_filter.filter_log_on_max_no_activities(log, max_no_activities=constants.MAX_NO_ACTIVITIES,
                                                            parameters=parameters)
    filtered_log = auto_filter.apply_auto_filter(log, parameters=parameters)

    activities_count = attributes_filter.get_attribute_values(filtered_log, activity_key)
    start_activities_count = start_activities_filter.get_start_activities(filtered_log, parameters=parameters)
    end_activities_count = end_activities_filter.get_end_activities(filtered_log, parameters=parameters)
    activities = list(activities_count.keys())
    start_activities = list(start_activities_count.keys())
    end_activities = list(end_activities_count.keys())

    dfg_freq = dfg_factory.apply(filtered_log, parameters=parameters)

    heu_net = HeuristicsNet(dfg_freq, activities=activities, start_activities=start_activities, end_activities=end_activities, activities_occurrences=activities_count)

    heu_net.calculate(dfg_pre_cleaning_noise_thresh=constants.DEFAULT_DFG_CLEAN_MULTIPLIER * decreasingFactor)

    vis = heu_vis_factory.apply(heu_net, parameters={"format": "svg"})
    vis2 = heu_vis_factory.apply(heu_net, parameters={"format": "dot"})

    gviz_base64 = get_base64_from_file(vis2.name)

    return get_base64_from_file(vis.name), None, "", "xes", activities, start_activities, end_activities, gviz_base64, [], "heuristics", "freq", None, "", activity_key
