#!/usr/bin/env python3
"""Check the single canonical project layout without changing native design files.

--inventory is for a Git-tree assembly before all unchanged blobs are downloaded.
By default every local dependency must exist on disk in the checkout.
"""
import argparse
import ast
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def check(inventory=None):
    known = set(inventory) if inventory is not None else None
    missing = []
    checked = set()

    def require(path):
        path = path.resolve()
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError:
            missing.append(str(path))
            return
        checked.add(relative)
        if (relative not in known) if known is not None else (not path.exists()):
            # Library URIs name directories, which Git does not store as blobs.
            if known is None or not any(p.startswith(relative + '/') for p in known):
                missing.append(relative)

    for base in ('hardware/nexus-style-fc', 'hardware/header-board/nexus-header-board'):
        for extension in ('.kicad_pro', '.kicad_sch', '.kicad_pcb', '.kicad_dru'):
            require(ROOT / (base + extension))
    for file in sorted((ROOT / 'tools').glob('*.py')):
        ast.parse(file.read_text(), filename=str(file))
    for file in sorted((ROOT / 'hardware').rglob('*')):
        # Editor histories are owner snapshots, not current project dependencies.
        if '.history' in file.relative_to(ROOT / 'hardware').parts:
            continue
        if not file.is_file() or file.suffix.lower() in ('.step', '.wrl'):
            continue
        if file.name.endswith('lib-table'):
            for uri in re.findall(r'\(uri "([^"]+)"\)', file.read_text()):
                if uri.startswith('${KIPRJMOD}/'):
                    require(file.parent / uri.removeprefix('${KIPRJMOD}/'))
        if file.suffix == '.kicad_pcb':
            for model in re.findall(r'\(model "([^"]+)"', file.read_text()):
                if model.startswith('${KIPRJMOD}/'):
                    require(file.parent / model.removeprefix('${KIPRJMOD}/'))
    require(ROOT / 'firmware/RDMS-NEXUS_F7.config')
    result = {'status': 'fail' if missing else 'pass', 'mode': 'git-tree inventory' if known is not None else 'checkout',
              'local_dependencies_checked': len(checked), 'missing': sorted(set(missing)),
              'note': 'Stock KiCad symbols, footprints and 3D models require KiCad 10 libraries. Model fit is not validated.'}
    print(json.dumps(result, indent=2))
    return bool(missing)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path)
    args = parser.parse_args()
    sys.exit(check(json.loads(args.inventory.read_text()) if args.inventory else None))
