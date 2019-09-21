from pm4py.visualization.common.utils import get_base64_from_gviz
from pm4py.visualization.dfg import factory as dfg_vis_factory
from pm4py.objects.conversion.dfg import factory as dfg_conv_factory

import base64
from pm4pyws.util import constants
from pm4py.objects.petri.exporter.pnml import export_petri_as_string
from pm4pyws.util import get_graph

from pm4py.algo.filtering.dfg.dfg_filtering import clean_dfg_based_on_noise_thresh

from pm4py.objects.log.util import xes

def apply(wrapper, parameters=None):
    if parameters is None:
        parameters = {}

    decreasingFactor = parameters["decreasingFactor"] if "decreasingFactor" in parameters else constants.DEFAULT_DEC_FACTOR

    obj = wrapper.calculate_composite_object(parameters={"performance_required": True})

    dfg = obj["frequency_dfg"]
    performance_dfg = obj["performance_dfg"]
    start_activities = list(obj["start_activities"].keys())
    end_activities = list(obj["end_activities"].keys())
    activities_count = obj["activities"]

    activities = list(activities_count.keys())

    dfg = clean_dfg_based_on_noise_thresh(dfg, activities, decreasingFactor * constants.DEFAULT_DFG_CLEAN_MULTIPLIER,
                                          parameters=parameters)
    max_acti_count = max(activities_count.values())
    activities_count = {x: y for x, y in activities_count.items() if y >= decreasingFactor * constants.DEFAULT_DFG_CLEAN_MULTIPLIER * max_acti_count}
    activities = list(activities_count.keys())
    dfg = {x: y for x, y in dfg.items() if x[0] in activities and x[1] in activities}
    performance_dfg = {x: y for x, y in performance_dfg.items() if x in dfg}

    gviz = dfg_vis_factory.apply(performance_dfg, variant="performance", activities_count=activities_count, parameters={"format": "svg", "start_activities": start_activities, "end_activities": end_activities})

    gviz_base64 = base64.b64encode(str(gviz).encode('utf-8'))

    ret_graph = get_graph.get_graph_from_dfg(dfg, start_activities, end_activities)

    net, im, fm = dfg_conv_factory.apply(dfg, parameters={"start_activities": start_activities, "end_activities": end_activities})

    return get_base64_from_gviz(gviz), export_petri_as_string(net, im, fm), ".pnml", "parquet", activities, start_activities, end_activities, gviz_base64, ret_graph, "dfg", "freq", None, "", xes.DEFAULT_NAME_KEY
