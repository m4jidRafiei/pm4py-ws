from pm4py.algo.discovery.inductive import factory as inductive_miner
from pm4py.visualization.common.utils import get_base64_from_gviz
from pm4py.visualization.process_tree import factory as pt_vis_factory
from pm4py.algo.filtering.log.auto_filter import auto_filter
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.util import constants as pm4_constants
from pm4py.objects.log.util import xes
from pm4py.algo.filtering.log.start_activities import start_activities_filter
from pm4py.algo.filtering.log.end_activities import end_activities_filter
import base64

from pm4pyws.util import constants

def apply(log, parameters=None):
    """
    Gets the process tree using Inductive Miner Directly-Follows

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

    activity_key = parameters[pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY] if pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY in parameters else xes.DEFAULT_NAME_KEY

    log = attributes_filter.filter_log_on_max_no_activities(log, max_no_activities=constants.MAX_NO_ACTIVITIES,
                                                            parameters=parameters)
    filtered_log = auto_filter.apply_auto_filter(log, parameters=parameters)

    activities_count = attributes_filter.get_attribute_values(filtered_log, activity_key)
    activities = list(activities_count.keys())
    start_activities = list(start_activities_filter.get_start_activities(filtered_log, parameters=parameters).keys())
    end_activities = list(end_activities_filter.get_end_activities(filtered_log, parameters=parameters).keys())

    tree = inductive_miner.apply_tree(filtered_log, parameters=parameters)
    parameters["format"] = "svg"
    gviz = pt_vis_factory.apply(tree, parameters=parameters)

    gviz_base64 = base64.b64encode(str(gviz).encode('utf-8'))

    return get_base64_from_gviz(gviz), None, "", "xes", activities, start_activities, end_activities, gviz_base64, []

