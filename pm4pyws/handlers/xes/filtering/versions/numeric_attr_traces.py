from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.util import constants


def apply(log, filter, parameters=None):
    """
    Apply a numeric filter (traces)

    Parameters
    -------------
    log
        log
    filter
        Filter to apply
    parameters
        Parameters of the algorithm

    Returns
    -------------
    log
        Filtered log
    """

    if parameters is None:
        parameters = {}

    parameters[constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY] = filter[1][0]

    min_value = float(filter[1][1].split("@@@")[0])
    max_value = float(filter[1][1].split("@@@")[1])

    return attributes_filter.apply_numeric(log, min_value, max_value, parameters=parameters)
