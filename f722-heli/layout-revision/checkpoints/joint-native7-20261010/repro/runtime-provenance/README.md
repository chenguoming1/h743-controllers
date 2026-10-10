# Isolated KiCad 10 runtime

Restored on 2026-10-09 from the official Debian sid repository. No system
packages or source PCB files were modified. All downloaded packages remain
under `packages/`; the extracted runtime is under `root/`.

## Entry points

- `./kicad-cli`: KiCad CLI 10.0.6 (DRC, ERC, export).
- `./python`: Python 3.14.8 with pcbnew 10.0.6 and the compatibility fix below.

Call these wrappers by absolute path from other directories. Do not invoke the
extracted binary directly or globally set `LD_LIBRARY_PATH`: the runtime uses
its own dynamic loader and libraries without changing the host environment.
Configuration, data, and caches remain inside this directory. The KiCad 10
official symbols and footprints and default library tables are installed here.
The wrappers do not provide extra third-party Python packages. 3D-model export
was not tested; the model path points to the host's optional KiCad model library.

## Validation

Against the recovered F722 source in `f722-layout-rebuild/repo/f722-heli/hardware`:

- CLI version: 10.0.6.
- pcbnew build: 10.0.6+dfsg-1.
- DRC: 0 errors and 0 unconnected items; 9 existing warnings (8 dangling track,
  1 dangling via). Reports: `verified-drc.json` and `smoke-drc-with-libraries.json`.
- ERC: 0 violations (`smoke-erc.json`).
- SVG export: succeeded (`smoke-board.svg`).
- LoadBoard, SaveBoard to an isolated copy, and reload: succeeded, preserving
  156 footprints, 2,672 track/via objects, 6 zones, and 130 net entries.
  The isolated output is `smoke-save.kicad_pcb`; this was a runtime test, not a
  design revision or a claim of fabrication readiness.

## Runtime adaptations

The private ELF loader causes KiCad to look for its editor plugins alongside
the loader. Relative symlinks in `root/usr/lib/x86_64-linux-gnu/` point to the
original extracted `.kiface` files in `root/usr/lib/kicad/`.

Debian's generated pcbnew SwigPyIterator provides `__next__`, but three KiCad
container helpers call `.next()`. `compat/sitecustomize.py` adds a Python method
alias at startup. It does not change compiled code, geometry, connectivity,
or board data. Run scripts using the `python` wrapper so the alias is active;
Python's `-S` option intentionally skips this startup customization.

## Provenance

Package source: https://deb.debian.org/debian/ .
Release source: https://deb.debian.org/debian/dists/sid/InRelease .

The release signatures verified against the installed Debian archive keyring
with both the Bookworm and Trixie archive signing keys. The release's SHA256
record matched the downloaded compressed package index. Every package's SHA256
was checked against that authenticated index. `package-manifest.json` records
exact package names, versions, URLs, and checksums. `fetch_packages.py` repeats
the signature, index, and individual-package verification before extracting
specified official packages within this directory.

This runtime intentionally reuses compatible host Debian 13 libraries; it is
not a standalone container or a cross-platform distribution.
