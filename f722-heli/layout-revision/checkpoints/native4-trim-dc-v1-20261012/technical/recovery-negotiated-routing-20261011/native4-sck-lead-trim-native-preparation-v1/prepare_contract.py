"""Bounded source validation only; no native imports or execution."""
import resource
from pathlib import Path
import native_trial as n
resource.setrlimit(resource.RLIMIT_AS,(536870912,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,61))
plan=n.guard.check_sources();old=n.read(plan['predecessor_contract'])
bound={**old['bound_files'],**plan['bindings'],**plan['immutable_predecessor_helpers']}
for path in [n.guard.PLAN,n.HERE/'native_trial.py',n.HERE/'stitch_guard.py',n.HERE/'compact_json.py',n.HERE/'paired_verify.py',Path(__file__).resolve(),n.HERE.parent/'source7-native5-sck-red-polygon-native-preparation-v2/structural_base.py']:bound[str(path.relative_to(n.ROOT))]=n.sha(path)
c={'schema':n.SCHEMA,'diagnostic_only':True,'accepted_or_adopted':False,'primary':'local_v1','variants':{'local_v1':{}},'resources':plan['resources'],'disk_budget':plan['disk_budget'],'native_build':'10.0.6+dfsg-1','native_exporter_error_iu':10,'source_board':plan['source_board'],'source_native':plan['source_native'],'source_auxiliary':plan['source_auxiliary'],'hardware':old['hardware'],'bound_files':bound,'return_stitch':n.guard.binding()}
n.validate_contract(c);output=n.HERE/'contract-two-track-trim-v3.json';n.write(output,c);print(n.sha(output));print('max_rss_KiB',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
