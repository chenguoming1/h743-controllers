#!/usr/bin/env python3
"""Remove dangling track / via stubs (from rip-ups) without breaking any connection.

  KiCad python:  clean_dangling.py BOARD DANGLING_UUIDS_FILE

A stub goes only if the exact (geometric) island count of its net stays the same without it; GND stubs
are kept (GND joins through the pours, which the island model does not include).
"""
import os
import sys

import pcbnew

os.environ.setdefault("ROUTE_PCB", sys.argv[1])
import finish_route as fr  # noqa: E402


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    ids = set(open(sys.argv[2]).read().split())
    model = fr.Model(board)
    removed = kept = 0
    for it in model.items:
        if it.kind == "pad" or it.obj.m_Uuid.AsString() not in ids or it.net in ("GND", "") or it.obj.IsLocked():
            continue
        before = model.islands(it.net)[1]
        it.removed = True
        if model.islands(it.net)[1] == before:
            removed += 1
        else:
            it.removed = False
            kept += 1
    for it in model.items:
        if it.removed and it.kind != "pad":
            board.Remove(it.obj)
    pcbnew.SaveBoard(sys.argv[1], board)
    print(f"removed {removed} stubs, kept {kept} that carry a connection")


if __name__ == "__main__":
    main()
