import base64
from pm4py.visualization.common.utils import get_base64_from_file
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.visualization.graphs import factory as graphs_factory


def get_numeric_attribute_distr_svg(log, attribute_key, parameters=None):
    """
    Gets the distribution of a numeric attribute values

    Parameters
    ------------
    log
        Log
    attribute_key
        Attribute that we are interested to consider
    parameters
        Possible parameters of the algorithm

    Returns
    -------------
    graph
        Case duration graph
    gviz_base64
        Base64 representation of the dot
    ret
        List of points
    """

    if parameters is None:
        parameters = {}

    x, y = attributes_filter.get_kde_numeric_attribute(log, attribute_key)

    gviz = graphs_factory.apply_plot(x, y, variant="attributes", parameters={"format": "svg"})

    gviz_base64 = base64.b64encode(str(gviz).encode('utf-8'))

    ret = []
    for i in range(len(x)):
        ret.append((x[i], y[i]))

    return get_base64_from_file(gviz), gviz_base64, ret

