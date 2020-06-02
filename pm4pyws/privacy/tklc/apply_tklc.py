import os
import random
import string
import sqlite3
import logging
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4pyws.handlers.xes.xes import XesHandler
from pp_role_mining.privacyPreserving import privacyPreserving
from copy import deepcopy

from p_tlkc_privacy.privacyPreserving import privacyPreserving
from pm4pywsconfiguration import configuration as Configuration
from datetime import datetime


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
    Apply TKLC
    """
    if parameters is None:
        parameters = {}

    L = [parameters["L"]] if "L" in parameters else 2
    C = [parameters["C"]] if "C" in parameters else 1
    K = [parameters["K"]] if "K" in parameters else 10
    K2 = [parameters["K2"]] if "K2" in parameters else 0.5
    sensitive = parameters["sensitive"] if "sensitive" in parameters else []
    T = [parameters["T"]] if "T" in parameters else ["minutes"]
    bk_type = parameters["bk_type"] if "bk_type" in parameters else "set"
    #L = [2]
    #C = [1]
    #K = [10]
    #K2 = [0.5]
    # sensitive = ['creator']
    #sensitive = []
    #T = ["minutes"]
    #cont = []
    #bk_type = "set"  # set, multiset, sequence, relative
    #privacy_aware_log_dir = "xes_results"
    #pp = privacyPreserving(event_log, "sepsis")
    #pp.apply(T, L, K, C, K2, sensitive, cont, bk_type, privacy_aware_log_dir)

    logging.error("L = "+str(L))
    logging.error("C = "+str(C))
    logging.error("K = "+str(K))
    logging.error("K2 = "+str(K2))
    logging.error("sensitive = "+str(sensitive))
    logging.error("T = "+str(T))
    logging.error("bk_type = "+str(bk_type))

    # gets the event log object
    xes_log_path = log_manager.get_handlers()[process]

    now = datetime.now()
    date_stru = now.strftime("%m-%d-%y %H-%M-%S")

    event_log_dirpath = Configuration.event_logs_path
    new_log_name = "TLKC "+date_stru+" "+process+" "+str(bk_type)+"_"+str(L[0])+"_"+str(K[0])+"_"+str(C[0])+"_"+str(K2[0])+"_"+str(T[0])

    logging.error("xes_log_path = "+str(xes_log_path))
    logging.error("new_log_name = "+str(new_log_name))
    logging.error("event_logs_path = "+str(event_log_dirpath))


    pp = privacyPreserving(xes_log_path, process)
    pp.apply(T, L, K, C, K2, sensitive, [], bk_type, event_log_dirpath, new_log_name)
    print(new_log_name)

    conn_logs = sqlite3.connect(log_manager.database_path)
    curs_logs = conn_logs.cursor()

    new_log_path = os.path.join(event_log_dirpath, new_log_name)
    if not os.path.exists(new_log_path):
        new_log_name = " "+new_log_name
        new_log_path = os.path.join(event_log_dirpath, new_log_name)
    logging.error("(used internally) new_log_path = "+str(new_log_path))
    curs_logs.execute("INSERT INTO EVENT_LOGS VALUES (?,?,0,1,1)", (new_log_name, new_log_path))
    conn_logs.commit()
    conn_logs.close()

    log_manager.logs_correspondence[new_log_name] = new_log_path

