import os
from pm4py.objects.log.exporter.xes import factory as xes_exporter


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

    # gets the event log object
    log = log_handler.log

    new_log_name = process + "_roles_privacy_" + generate_random_string(4)
    new_log_path = os.path.join("logs", new_log_name + ".xes")

    xes_exporter.export_log(log, new_log_path)

    conn_logs = sqlite3.connect(self.database_path)
    curs_logs = conn_logs.cursor()

    curs_logs.execute("INSERT INTO EVENT_LOGS VALUES (?,?,0,1,1)", (new_log_name, new_log_path))
    conn_logs.commit()
    conn_logs.close()
