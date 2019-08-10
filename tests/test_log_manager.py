from pm4pyws.user_iam import factory as user_iam_factory
from pm4pyws.requests_logging import factory as exception_factory
from pm4pyws.log_manager import factory as lm_factory
import unittest


class TestLogManager(unittest.TestCase):
    def test_log_manager(self):
        ex = exception_factory.apply()
        sm = user_iam_factory.apply(ex)
        lm = lm_factory.apply(ex)
        lm.set_user_management(sm)
        all_sessions = sm.get_all_sessions()
        lm.remove_unneeded_sessions(all_sessions)
        lm.get_handlers()
        lm.check_is_admin("admin")
        lm.check_user_log_visibility("admin", "receipt")
        lm.check_user_enabled_upload("user1")
        lm.check_user_enabled_upload("user2")
        lm.check_user_enabled_download("user1", "receipt")
        lm.check_user_enabled_download("user2", "running-example")
        lm.load_log_static("receipt", "files/event_logs/receipt.parquet")
        lm.load_log_static("receipt", "files/event_logs/receipt.xes")
        lm.save_object_memory("ciao", "ciao")
        var = lm.get_object_memory("ciao")
        lm.get_user_eventlog_vis_down_remov()
        lm.add_user_eventlog_visibility("admin", "receipt")
        lm.remove_user_eventlog_visibility("admin", "receipt")
        lm.add_user_eventlog_downloadable("admin", "receipt")
        lm.remove_user_eventlog_downloadable("admin", "receipt")
        lm.add_user_eventlog_removable("admin", "receipt")
        lm.remove_user_eventlog_removable("admin", "receipt")


if __name__ == "__main__":
    unittest.main()
