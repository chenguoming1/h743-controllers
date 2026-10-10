"""Compatibility for KiCad 10.0.6's SWIG iteration helper.

Debian's generated SwigPyIterator uses __next__, while three container
helpers in pcbnew still call .next(). Alias the Python method only; no
KiCad binary, geometry, connectivity, or file content is changed.
"""
import pcbnew

if not hasattr(pcbnew.SwigPyIterator, "next"):
    pcbnew.SwigPyIterator.next = pcbnew.SwigPyIterator.__next__
