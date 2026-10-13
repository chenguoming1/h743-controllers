# Nominal assembly replay

Run `python -B replay.py` from any working directory for hash/source checks only. For a new geometry result, use `python -B replay.py --run --work /path/to/new-output-directory` with POSIX Python 3.11 and Shapely 2.2.0 installed. The launcher requires a new output directory and uses a local replay lock. It writes only there and uses source symlinks to the selected published hardware/native bytes.

`SOURCE-NORMALIZATION.json` records the original script identity and path-only substitutions. Every computational AST statement beginning with the `sha` helper remains identical to the originally executed script. A fresh output is compared with the original technical JSON after excluding only peak RSS and script identity. The original result is included byte-exact. The report separately preserves nominal geometry and manufacturing limits.

Source/hash checks and AST/syntax checks were tested for this package. The adapted geometry execution has not been run. No other historical native file or helper is required.
