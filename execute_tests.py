import inspect
import os
import sys
import unittest

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

    from tests.test_parquet_handler import ParquetTests
    from tests.test_parquet_handler_lazy import ParquetTestsLazy
    from tests.test_log_handler import XesTests
    from tests.test_session import SessionTest
    from tests.test_log_manager import TestLogManager
    from tests.test_exc import ExceptionHandlTest
    from tests.test_csv_handler import CsvTests

    tp = ParquetTests()
    tpl = ParquetTestsLazy()
    tx = XesTests()
    st = SessionTest()
    lmt = TestLogManager()
    eht = ExceptionHandlTest()
    csv = CsvTests()

    unittest.main()
