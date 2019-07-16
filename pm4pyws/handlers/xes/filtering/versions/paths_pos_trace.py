from pm4py.algo.filtering.log.paths import paths_filter
from pm4py.util import constants


def apply(dataframe, filter, parameters=None):
    """
    Apply a filter to the current log (paths filter)

    Parameters
    ------------
    log
        Event log
    filter
        Filter to apply
    parameters
        Parameters of the algorithm

    Returns
    ------------
    log
        Event log
    """
    if parameters is None:
        parameters = {}

    parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = filter[1][0]
    parameters["positive"] = True

    paths_to_filter = []

    for p in filter[1][1]:
        paths_to_filter.append(tuple(p.split("@@")))

    return paths_filter.apply(dataframe, paths_to_filter, parameters=parameters)
