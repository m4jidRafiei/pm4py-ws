from p_connector_dfg.privacyPreserving import privacyPreserving
from copy import deepcopy
import random
import string
import os
from pm4pywsconfiguration import configuration as Configuration
import sqlite3


def generate_random_string(N):
    """
    Generates a random string

    Parameters
    ------------
    N
        Length of the string

    Returns
    -------------
    random_stri
        Random string (of length N)
    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

def apply(process, log_manager, parameters=None):
    if parameters is None:
        parameters = {}

    xes_log_path = log_manager.get_handlers()[process]

    pma_method = "Connector Method"
    pma_desired_analyses = ['Directly Follows Graph']

    relation_depth = parameters["relation_depth"] if "relation_depth" in parameters else True
    trace_length = parameters["trace_length"] if "trace_length" in parameters else True
    trace_id = parameters["trace_id"] if "trace_id" in parameters else True

    new_log_name = xes_log_path.split("/event_logs/")[1] + "@@connector@@" + generate_random_string(4)
    new_log_path = os.path.join(Configuration.event_logs_path, new_log_name + ".xml")

    pp = privacyPreserving(deepcopy(xes_log_path))

    pp.apply_privacyPreserving(new_log_path, pma_method, pma_desired_analyses, xes_log_path, relation_depth=relation_depth, trace_length=trace_length, trace_id=trace_id)

    conn_logs = sqlite3.connect(log_manager.database_path)
    curs_logs = conn_logs.cursor()

    curs_logs.execute("INSERT INTO EVENT_LOGS VALUES (?,?,0,1,1)", (new_log_name, new_log_path))
    conn_logs.commit()
    conn_logs.close()

    log_manager.logs_correspondence[new_log_name] = new_log_path
