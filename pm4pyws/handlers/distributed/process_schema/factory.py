from pm4pyws.handlers.distributed.process_schema.dfg_freq import get_vis as dfg_freq_vis
from pm4pyws.handlers.distributed.process_schema.dfg_perf import get_vis as dfg_perf_vis
from pm4pyws.handlers.distributed.process_schema.heuristics_freq import get_vis as heu_freq_vis
from pm4pyws.handlers.distributed.process_schema.heuristics_perf import get_vis as heu_perf_vis
from pm4pyws.handlers.distributed.process_schema.inductive_freq import get_vis as inductive_freq_vis
from pm4pyws.handlers.distributed.process_schema.inductive_perf import get_vis as inductive_perf_vis
from pm4pyws.handlers.distributed.process_schema.tree import get_vis as tree_vis

from pm4pywsconfiguration import configuration as Configuration


DFG_FREQ = "dfg_freq"
DFG_PERF = "dfg_perf"
TREE_FREQ = "tree_freq"
TREE_PERF = "tree_perf"
INDUCTIVE_FREQ = "inductive_freq"
INDUCTIVE_PERF = "inductive_perf"
HEURISTICS_FREQ = "heuristics_freq"
HEURISTICS_PERF = "heuristics_perf"

VERSIONS = {DFG_FREQ: dfg_freq_vis.apply, DFG_PERF: dfg_perf_vis.apply, TREE_FREQ: tree_vis.apply,
            TREE_PERF: tree_vis.apply, INDUCTIVE_FREQ: inductive_freq_vis.apply,
            INDUCTIVE_PERF: inductive_perf_vis.apply, HEURISTICS_FREQ: heu_freq_vis.apply, HEURISTICS_PERF: heu_perf_vis.apply}

try:
    import pm4pybpmn
    Configuration.enable_bpmn = True
except:
    Configuration.enable_bpmn = False

if Configuration.enable_bpmn:
    from pm4pyws.handlers.parquet.process_schema.indbpmn_freq import get_vis as indbpmn_freq_vis
    from pm4pyws.handlers.parquet.process_schema.indbpmn_perf import get_vis as indbpmn_perf_vis

    INDBPMN_FREQ = "indbpmn_freq"
    INDBPMN_PERF = "indbpmn_perf"

    VERSIONS[INDBPMN_FREQ] = indbpmn_freq_vis.apply
    VERSIONS[INDUCTIVE_PERF] = indbpmn_perf_vis.apply


def apply(wrapper, variant=DFG_FREQ, parameters=None):
    return VERSIONS[variant](wrapper, parameters=parameters)
