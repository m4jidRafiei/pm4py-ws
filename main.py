import requests

try:
    import pm4pycvxopt
except:
    pass

from pm4pyws.entrypoint import PM4PyServices

import sqlite3
conn_event_logs = sqlite3.connect('event_logs.db')
cursor_event_logs = conn_event_logs.cursor()

# local host of the current machine
THIS_HOST = "127.0.0.1"
# host that shall be listening (0.0.0.0 means accepting connections from everything)
LISTENING_HOST = "0.0.0.0"
# listen to this port
LISTENING_PORT = 5000

if __name__ == "__main__":
    try:
        # try to see if the service is alive, in that case just try to add the 'receipt'
        # process to the list
        r = requests.post("http://" + THIS_HOST + ":" + str(LISTENING_PORT) + "/loadLogFromPath",
                          json={"log_name": "receipt",
                                "log_path": "receipt.parquet"})
        print("service listening, told to load the log, response: " + str(r.text))
    except:
        # otherwise, the service is not listening and it needs to be boot up
        print("service not listening, booting it up")
        S = PM4PyServices()
        cursor_event_logs.execute("SELECT LOG_NAME, LOG_PATH FROM EVENT_LOGS WHERE LOADED_BOOT = 1")
        for result in cursor_event_logs.fetchall():
            S.load_log(str(result[0]), str(result[1]))

        conn_event_logs.close()

        # offers the service to the outside
        S.serve(host=LISTENING_HOST, port=LISTENING_PORT)
