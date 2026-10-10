"""Select explicit nets for the unchanged native reference geometry tools.

This broadens geometric inspection only. It does not change shapes, clearance
rules, reference windows or acceptance thresholds, and grants no qualification.
"""
import argparse,importlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--mode',choices=['export','review','compare'],required=True)
p.add_argument('--targets',type=Path,required=True)
a,remaining=p.parse_known_args()
targets=json.loads(a.targets.read_text())['nets']
if not targets or targets!=sorted(set(targets)) or any(not isinstance(n,str) or n in ('','GND') for n in targets):
    raise ValueError('Explicit unique non-GND target nets required')
sys.path.insert(0,str(R/'repo/f722-heli/layout-revision/signal-review/native'))
module=importlib.import_module({'export':'export_signal_snapshot','review':'check_critical_reference','compare':'compare_reference_geometry'}[a.mode])
module.I2C={};module.CRITICAL=targets
sys.argv=[sys.argv[0],*remaining]
module.main()
