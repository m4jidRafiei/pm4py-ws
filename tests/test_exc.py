import unittest
from pm4pyws.requests_logging import factory as exception_factory


class ExceptionHandlTest(unittest.TestCase):
    def test_exc(self):
        ex = exception_factory.apply()
        ex.debug("msg")
        ex.info("msg")
        ex.warning("msg")
        ex.error("msg")


if __name__ == "__main__":
    unittest.main()
