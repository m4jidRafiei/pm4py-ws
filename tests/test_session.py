from pm4pyws.user_iam import factory as user_iam_factory
from pm4pyws.requests_logging import factory as exception_factory
import unittest


class SessionTest(unittest.TestCase):
    def test_session(self):
        ex = exception_factory.apply()
        sm = user_iam_factory.apply(ex)
        session = sm.do_login("admin", "admin")
        sm.check_session_validity(session)
        sm.get_user_from_session(session)
        sm.clean_expired_sessions()
        sm.get_all_sessions()
        sm.get_all_users()


if __name__ == "__main__":
    unittest.main()
