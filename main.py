import requests

try:
    import pm4pycvxopt
except:
    pass

from pm4pyws.entrypoint import PM4PyServices

app = PM4PyServices.app

import sqlite3
conn_event_logs = sqlite3.connect('event_logs.db')
cursor_event_logs = conn_event_logs.cursor()
S = PM4PyServices()
cursor_event_logs.execute("SELECT LOG_NAME, LOG_PATH FROM EVENT_LOGS WHERE LOADED_BOOT = 1")
for result in cursor_event_logs.fetchall():
    S.load_log(str(result[0]), str(result[1]))
conn_event_logs.close()

# offers the service to the outside
if __name__ == "__main__":
    LISTENING_HOST = "0.0.0.0"
    LISTENING_PORT = 5000
    S.serve(host=LISTENING_HOST, port=LISTENING_PORT)
