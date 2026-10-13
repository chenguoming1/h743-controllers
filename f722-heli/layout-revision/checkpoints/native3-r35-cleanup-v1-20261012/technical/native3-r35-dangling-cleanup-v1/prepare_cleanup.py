"""Non-executing source excerpts. See SOURCE-PROVENANCE.json for original identity.
Dependencies belong to the original implementation; use reproduction/replay_native.py
for the standalone verifier and exact sealed-recipe replay.
"""

def load(p,h):
 raw=gzip.open(p,'rb').read();assert hashlib.sha256(raw).hexdigest()==h;v=json.loads(raw);return v
