import os
import random
import string
import sqlite3
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4pyws.handlers.xes.xes import XesHandler
from pp_role_mining.privacyPreserving import privacyPreserving
from copy import deepcopy

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


def apply(process, log_handler, log_manager, user_manager, exc_handler, parameters=None):
    """
    Apply privacy aware process mining
    """
    if parameters is None:
        parameters = {}

    no_substitutions = parameters["no_substitutions"]
    selective_lower_bound_applied = parameters["selective_lower_bound_applied"]
    selective_upper_bound_applied = parameters["selective_upper_bound_applied"]
    fixed_value = parameters["fixed_value"]
    technique = parameters["technique"]
    resource_aware = parameters["resource_aware"]
    hashed_activities = parameters["hashed_activities"]
    event_attributes2remove = parameters["event_attributes2remove"]
    trace_attributes2remove = parameters["trace_attributes2remove"]

    print("no_substitutions=",no_substitutions)
    print("selective_lower_bound_applied=",selective_lower_bound_applied)
    print("selective_upper_bound_applied=",selective_upper_bound_applied)
    print("fixed_value=",fixed_value)
    print("technique",technique)
    print("resource_aware",resource_aware)
    print("hashed_activities",hashed_activities)
    print("event_attributes2remove",event_attributes2remove)
    print("trace_attributes2remove",trace_attributes2remove)
    #input()

    # gets the event log object
    log = log_handler.log

    new_log_name = process + "_roles_privacy_" + generate_random_string(4)
    new_log_path = os.path.join("logs", new_log_name + ".xes")

    # xes_exporter.export_log(log, new_log_path)

    pp = privacyPreserving(deepcopy(log))
    pp.apply_privacyPreserving(technique, resource_aware, True, False, hashed_activities,
                               NoSubstitutions=no_substitutions,
                               MinMax=[selective_lower_bound_applied, selective_upper_bound_applied],
                               FixedValue=fixed_value,
                               privacy_aware_log_path=new_log_path,
                               event_attribute2remove=event_attributes2remove,
                               case_attribute2remove=trace_attributes2remove)

    conn_logs = sqlite3.connect(log_manager.database_path)
    curs_logs = conn_logs.cursor()

    curs_logs.execute("INSERT INTO EVENT_LOGS VALUES (?,?,0,1,1)", (new_log_name, new_log_path))
    conn_logs.commit()
    conn_logs.close()

    handler = XesHandler()
    handler.build_from_path(new_log_path)

    log_manager.handlers[new_log_name] = handler
