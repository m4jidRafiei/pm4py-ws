import sqlite3
import os
import shutil
import urllib.request

logs_to_download = {
    "receipt": "http://www.alessandroberti.it/receipt.parquet",
    "roadtraffic": "http://www.alessandroberti.it/roadtraffic.parquet",
    "bpic2017": "http://www.alessandroberti.it/bpic2017.parquet",
    "bpic2017_application": "http://www.alessandroberti.it/bpic2017_application.parquet",
    "bpic2018": "http://www.alessandroberti.it/bpic2018.parquet",
    "bpic2019": "http://www.alessandroberti.it/bpic2019.parquet"
}

shutil.rmtree("event_logs")
os.mkdir("event_logs")

conn = sqlite3.connect("databases/event_logs.db")
curs = conn.cursor()

curs.execute("DELETE FROM EVENT_LOGS")
curs.execute("DELETE FROM USER_LOG_DOWNLOADABLE")
curs.execute("DELETE FROM USER_LOG_REMOVAL")
curs.execute("DELETE FROM USER_LOG_VISIBILITY")

for log in logs_to_download:
    url = logs_to_download[log]
    urllib.request.urlretrieve(url, "event_logs/"+log+".parquet")

    curs.execute("INSERT INTO EVENT_LOGS VALUES ('"+log+"','files/event_logs/"+log+".parquet',0,1,0)")
    print("downloaded and inserted "+log)

conn.commit()
conn.close()