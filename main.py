try:
    import pm4pycvxopt
except:
    pass
from time import sleep

from pm4pyws.entrypoint import PM4PyServices
from pm4pywsconfiguration import configuration as Configuration
from pm4pyws.handlers.distributed.distributed import DistributedHandler
import os

app = PM4PyServices.app

#import sqlite3
#conn_event_logs = sqlite3.connect(Configuration.event_log_db_path)
#cursor_event_logs = conn_event_logs.cursor()
#S = PM4PyServices()
#cursor_event_logs.execute("SELECT LOG_NAME, LOG_PATH FROM EVENT_LOGS WHERE LOADED_BOOT = 1")
#for result in cursor_event_logs.fetchall():
#    S.load_log(str(result[0]), str(result[1]))
#conn_event_logs.close()

print("sleeping")
sleep(10)

S = PM4PyServices()
pm4pydistr_master_host = os.environ["pm4pydistrmasterhost"] if "pm4pydistrmasterhost" in os.environ else Configuration.default_pm4pydistr_master_host
pm4pydistr_master_port = os.environ["pm4pydistrmasterport"] if "pm4pydistrmasterport" in os.environ else Configuration.default_pm4pydistr_master_port
pm4pydistr_keyphrase = os.environ["pm4pydistrkeyphrase"] if "pm4pydistrkeyphrase" in os.environ else Configuration.default_pm4pydistr_keyphrase


from pm4pydistr.remote_wrapper import factory as rw_factory
wrapper = rw_factory.apply(pm4pydistr_master_host, pm4pydistr_master_port, pm4pydistr_keyphrase, "dummy")
list_logs = wrapper.get_logs_list()
for log in list_logs:
    wrapper = rw_factory.apply(pm4pydistr_master_host, pm4pydistr_master_port, pm4pydistr_keyphrase, log)
    wrapper.do_caching()
    handler = DistributedHandler(wrapper)
    S.add_handler(log+"(distributed)", handler)

there_is_ssl_context = False
CERT_FILE = "this.crt"
PRIVATE_KEY_FILE = "this.key"

try:
    content = os.listdir(Configuration.ssl_context_directory)
    if CERT_FILE in content and PRIVATE_KEY_FILE in content:
        there_is_ssl_context = True
except:
    pass

print("there_is_ssl_context", there_is_ssl_context)

# offers the service to the outside
if __name__ == "__main__":
    if not there_is_ssl_context:
        LISTENING_HOST = "0.0.0.0"
        LISTENING_PORT = 5000
        S.serve(host=LISTENING_HOST, port=LISTENING_PORT)
    else:
        LISTENING_HOST = "0.0.0.0"
        LISTENING_PORT = 5443
        CERT_FILE = os.path.join(Configuration.ssl_context_directory, CERT_FILE)
        PRIVATE_KEY_FILE = os.path.join(Configuration.ssl_context_directory, PRIVATE_KEY_FILE)
        S.serve(host=LISTENING_HOST, port=LISTENING_PORT, ssl_context=(CERT_FILE, PRIVATE_KEY_FILE))
