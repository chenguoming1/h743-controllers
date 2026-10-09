"""Error-type compatibility shim ONLY; this is not the copper field solver.

The unchanged dc_circuit.py imports this one exception. No native geometry,
mesh, field, SciPy or Shapely implementation is shipped or callable here.
The omitted original field module's identity is recorded in source-identities.json.
"""
class Refused(RuntimeError):
    pass
