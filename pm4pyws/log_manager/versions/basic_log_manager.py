import sqlite3

from pm4pyws.configuration import Configuration
from pm4pyws.handlers.parquet.parquet import ParquetHandler
from pm4pyws.handlers.xes.xes import XesHandler
from pm4pyws.log_manager.interface.log_manager import LogHandler

import time


class BasicLogSessionHandler(LogHandler):
    def __init__(self, ex):
        # path to the database
        self.database_path = "event_logs.db"

        self.handlers = {}
        self.session_handlers = {}

        self.objects_memory = {}
        self.objects_timestamp = {}

        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()
        curs_logs.execute("DELETE FROM EVENT_LOGS WHERE IS_TEMPORARY = 1")
        conn_logs.commit()

        LogHandler.__init__(self, ex)

    def remove_unneeded_sessions(self, all_sessions):
        """
        Remove expired sessions

        Parameters
        ------------
        all_sessions
            All valid sessions
        """
        shk = list(self.session_handlers.keys())
        for session in shk:
            if session not in all_sessions and (not str(session) == "null"):
                print("removing handler for " + session)
                del self.session_handlers[session]

    def get_handlers(self):
        """
        Gets the current set of handlers

        Returns
        -----------
        handlers
            Handlers
        """
        return self.handlers

    def get_handler_for_process_and_session(self, process, session):
        """
        Gets an handler for a given process and session

        Parameters
        -------------
        process
            Process
        session
            Session

        Returns
        -------------
        handler
            Handler
        """
        if process in self.handlers:
            if session not in self.session_handlers:
                self.session_handlers[session] = {}
            if process not in self.session_handlers[session]:
                self.session_handlers[session][process] = self.handlers[process]
            # print(LogsHandlers.session_handlers[session][process].filters_chain)
            return self.session_handlers[session][process]
        return None

    def set_handler_for_process_and_session(self, process, session, handler):
        """
        Sets the handler for the current process and session

        Parameters
        -------------
        process
            Process
        session
            Session
        handler
            Handler
        """
        if process in self.handlers:
            if session not in self.session_handlers:
                self.session_handlers[session] = {}
            self.session_handlers[session][process] = handler

    def check_is_admin(self, user):
        """
        Checks if the user is an administrator

        Parameters
        -------------
        user
            User

        Returns
        -------------
        boolean
            Boolean value
        """
        if Configuration.enable_session:
            conn_logs = sqlite3.connect(self.database_path)
            curs_logs = conn_logs.cursor()
            curs_logs.execute("SELECT USER_ID FROM ADMINS WHERE USER_ID = ? AND USER_ID = ?", (user, user))
            results = curs_logs.fetchone()
            if results is not None:
                return True
            return False
        return True

    def manage_upload(self, user, basename, filepath, is_temporary=False):
        """
        Manages an event log that is uploaded

        Parameters
        ------------
        user
            Current user
        basename
            Name of the log
        filepath
            Log path
        """

        if filepath.endswith(".parquet"):
            self.handlers[basename] = ParquetHandler()
            self.handlers[basename].build_from_path(filepath)
        elif filepath.endswith(".csv"):
            self.handlers[basename] = ParquetHandler()
            self.handlers[basename].build_from_csv(filepath)
        else:
            self.handlers[basename] = XesHandler()
            self.handlers[basename].build_from_path(filepath)
        conn_logs = sqlite3.connect(self.database_path)
        curs_logs = conn_logs.cursor()
        if is_temporary:
            curs_logs.execute("INSERT INTO EVENT_LOGS VALUES (?,?,1,0,1)", (basename, filepath))
        else:
            curs_logs.execute("INSERT INTO EVENT_LOGS VALUES (?,?,0,1,1)", (basename, filepath))
        curs_logs.execute("INSERT INTO USER_LOG_VISIBILITY VALUES (?,?)", (user, basename))
        curs_logs.execute("INSERT INTO USER_LOG_DOWNLOADABLE VALUES (?,?)", (user, basename))
        curs_logs.execute("INSERT INTO USER_LOG_REMOVAL VALUES (?,?)", (user, basename))
        conn_logs.commit()
        conn_logs.close()

    def check_user_log_visibility(self, user, process):
        """
        Checks if the user has visibility on the given process

        Parameters
        -------------
        user
            User
        process
            Process
        """
        if Configuration.enable_session:
            conn_logs = sqlite3.connect(self.database_path)
            curs_logs = conn_logs.cursor()
            curs_logs.execute("SELECT USER_ID FROM USER_LOG_VISIBILITY WHERE USER_ID = ? AND LOG_NAME = ?",
                              (user, process))
            results = curs_logs.fetchone()
            if results is not None:
                return True
            return self.check_is_admin(user)
        return True

    def check_user_enabled_upload(self, user):
        """
        Checks if the user is enabled to upload a log

        Parameters
        ------------
        user
            User

        Returns
        ------------
        boolean
            Boolean value
        """
        if Configuration.enable_session:
            conn_logs = sqlite3.connect(self.database_path)
            curs_logs = conn_logs.cursor()
            curs_logs.execute("SELECT USER_ID FROM USER_UPLOADABLE WHERE USER_ID = ? AND USER_ID = ?", (user, user))
            results = curs_logs.fetchone()
            if results is not None:
                return True
            return self.check_is_admin(user)
        return True

    def check_user_enabled_download(self, user, process):
        """
        Checks if the user is enabled to download a log

        Parameters
        ------------
        user
            User
        process
            Process

        Returns
        ------------
        boolean
            Boolean value
        """
        if Configuration.enable_session:
            conn_logs = sqlite3.connect(self.database_path)
            curs_logs = conn_logs.cursor()
            curs_logs.execute("SELECT USER_ID FROM USER_LOG_DOWNLOADABLE WHERE USER_ID = ? AND LOG_NAME = ?",
                              (user, process))
            results = curs_logs.fetchone()
            if results is not None:
                return True
            return self.check_is_admin(user)
        return True

    def load_log_static(self, log_name, file_path, parameters=None):
        """
        Loads an event log inside the known handlers

        Parameters
        ------------
        log_name
            Log name
        file_path
            Full path (in the services machine) to the log
        parameters
            Possible parameters
        """
        if log_name not in self.handlers:
            if file_path.endswith(".parquet"):
                self.handlers[log_name] = ParquetHandler()
                self.handlers[log_name].build_from_path(file_path, parameters=parameters)
            elif file_path.endswith(".csv"):
                self.handlers[log_name] = ParquetHandler()
                self.handlers[log_name].build_from_csv(file_path, parameters=parameters)
            elif file_path.endswith(".xes") or file_path.endswith(".xes.gz"):
                self.handlers[log_name] = XesHandler()
                self.handlers[log_name].build_from_path(file_path, parameters=parameters)

    def save_object_memory(self, key, value):
        """
        Saves an object into the objects memory

        Parameters
        ------------
        key
            Key
        value
            Value
        """
        self.objects_memory[key] = value
        self.objects_timestamp[key] = time.time()

    def get_object_memory(self, key):
        """
        Gets an object from the objects memory

        Parameters
        ------------
        key
            Key
        value
            Value
        """
        if key in self.objects_memory:
            return self.objects_memory[key]
        return None
