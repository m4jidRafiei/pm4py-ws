from pm4pyws.handlers.xes.filtering.versions import start_activities, end_activities, attributes_pos_trace, \
    attributes_neg_trace, attributes_pos_events, attributes_neg_events, variants, timestamp_events, \
    timestamp_trace_containing, timestamp_trace_intersecting, case_performance_filter, numeric_attr_events, numeric_attr_traces, paths_pos_trace, paths_neg_trace


def apply(log, filter, parameters=None):
    """
    Apply a filter to the current log (factory method)

    Parameters
    ------------
    log
        Log object
    filter
        Filter to apply
    parameters
        Parameters of the algorithm

    Returns
    ------------
    log
        Log object
    """
    if parameters is None:
        parameters = {}

    if filter[0] == "start_activities":
        return start_activities.apply(log, filter, parameters=parameters)
    elif filter[0] == "end_activities":
        return end_activities.apply(log, filter, parameters=parameters)
    elif filter[0] == "attributes_pos_trace":
        return attributes_pos_trace.apply(log, filter, parameters=parameters)
    elif filter[0] == "attributes_neg_trace":
        return attributes_neg_trace.apply(log, filter, parameters=parameters)
    elif filter[0] == "attributes_pos_events":
        return attributes_pos_events.apply(log, filter, parameters=parameters)
    elif filter[0] == "attributes_neg_events":
        return attributes_neg_events.apply(log, filter, parameters=parameters)
    elif filter[0] == "variants":
        return variants.apply(log, filter, parameters=parameters)
    elif filter[0] == "timestamp_events":
        return timestamp_events.apply(log, filter, parameters=parameters)
    elif filter[0] == "timestamp_trace_containing":
        return timestamp_trace_containing.apply(log, filter, parameters=parameters)
    elif filter[0] == "timestamp_trace_intersecting":
        return timestamp_trace_intersecting.apply(log, filter, parameters=parameters)
    elif filter[0] == "case_performance_filter":
        return case_performance_filter.apply(log, filter, parameters=parameters)
    elif filter[0] == "numeric_attr_traces":
        return numeric_attr_traces.apply(log, filter, parameters=parameters)
    elif filter[0] == "numeric_attr_events":
        return numeric_attr_events.apply(log, filter, parameters=parameters)
    elif filter[0] == "paths_pos_trace":
        return paths_pos_trace.apply(log, filter, parameters=parameters)
    elif filter[0] == "paths_neg_trace":
        return paths_neg_trace.apply(log, filter, parameters=parameters)

    return log
