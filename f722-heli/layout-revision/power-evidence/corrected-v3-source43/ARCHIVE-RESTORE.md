# Reconstruct the frozen-input archive before verification

The exact frozen-inputs.tar.gz is stored losslessly in [frozen-inputs.parts](frozen-inputs.parts/README.md) to fit the publication transport limit. Run `python3 frozen-inputs.parts/restore.py` here, then follow the unchanged [historical package verification instructions](README.md). All original hashes and evidence remain unchanged.
