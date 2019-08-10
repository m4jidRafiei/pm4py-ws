import os
import unittest

from pm4pyws.handlers.parquet.parquet import ParquetHandler


def basic_test(path):
    handler = ParquetHandler()
    handler.build_from_path(path)
    handler.get_schema(variant="dfg_freq")
    handler.get_schema(variant="dfg_perf")
    handler.get_schema(variant="inductive_freq")
    handler.get_schema(variant="inductive_perf")
    handler.get_schema(variant="heuristics_freq")
    handler.get_schema(variant="heuristics_perf")
    handler.get_schema(variant="tree_freq")
    handler.get_schema(variant="tree_perf")
    handler.get_case_duration_svg()
    handler.get_events_per_time_svg()
    handler.get_sna(variant="handover")
    handler.get_sna(variant="working_together")
    handler.get_sna(variant="subcontracting")
    handler.get_sna(variant="jointactivities")
    handler.get_transient(86400)


def process_quantities_test(path):
    handler = ParquetHandler()
    handler.build_from_path(path)
    handler.get_start_activities()
    handler.get_end_activities()
    handler.get_variant_statistics()
    cases = handler.get_case_statistics()
    case_id_0 = cases[0]['caseId']
    handler.get_variant_statistics()
    handler.get_paths("concept:name")
    handler.get_attribute_values("concept:name")
    handler.get_events(case_id_0)


class ParquetTests(unittest.TestCase):
    def test_parquets_basic(self):
        basic_test("files/event_logs/running-example.parquet")
        basic_test("files/event_logs/receipt.parquet")

    def test_parquets_process_quantities(self):
        process_quantities_test("files/event_logs/running-example.parquet")
        process_quantities_test("files/event_logs/receipt.parquet")

    def test_ru_filtering(self):
        handler = ParquetHandler()
        handler.build_from_path("files/event_logs/running-example.parquet")
        handler = handler.add_filter(['timestamp_trace_intersecting', '1293703320@@@1294667760'],
                                     ['timestamp_trace_intersecting', '1293703320@@@1294667760'])
        handler.get_start_activities()
        handler.get_end_activities()
        handler.get_variant_statistics()
        handler = handler.add_filter(['timestamp_trace_containing', '1293703320@@@1294667760'],
                                     [['timestamp_trace_intersecting', '1293703320@@@1294667760'],
                                      ['timestamp_trace_containing', '1293703320@@@1294667760']])
        handler.get_start_activities()
        handler.get_end_activities()
        handler.get_variant_statistics()
        handler = handler.remove_filter(['timestamp_trace_containing', '1293703320@@@1294667760'],
                                        [['timestamp_trace_intersecting', '1293703320@@@1294667760']])
        handler.get_start_activities()
        handler.get_end_activities()
        handler.get_variant_statistics()
        handler = handler.remove_filter(['timestamp_trace_intersecting', '1293703320@@@1294667760'], [])
        handler.get_start_activities()
        handler.get_end_activities()
        handler.get_variant_statistics()
        handler = handler.add_filter(['end_activities', ['reject request']], [['end_activities', ['reject request']]])
        handler.get_start_activities()
        handler.get_end_activities()
        handler.get_variant_statistics()
        handler = handler.add_filter(['attributes_pos_trace', ['concept:name', ['check ticket']]],
                                     [['end_activities', ['reject request']],
                                      ['attributes_pos_trace', ['concept:name', ['check ticket']]]])
        handler.get_start_activities()
        handler.get_end_activities()
        handler.get_variant_statistics()
        handler = handler.remove_filter(['attributes_pos_trace', ['concept:name', ['check ticket']]],
                                        [['end_activities', ['reject request']]])
        handler = handler.remove_filter(['end_activities', ['reject request']], [])
        handler.get_start_activities()
        handler.get_end_activities()
        handler.get_variant_statistics()


if __name__ == "__main__":
    unittest.main()
