from pm4pyws.handlers.xes.process_schema import dfg_freq, dfg_perf, inductive_freq, \
    inductive_perf, heuristics_freq, util

from pm4pyws import configuration as Configuration

try:
    import pm4pybpmn
    Configuration.enable_bpmn = True
except:
    Configuration.enable_bpmn = False

if Configuration.enable_bpmn:
    from pm4pyws.handlers.parquet.process_schema import indbpmn_freq, indbpmn_perf
