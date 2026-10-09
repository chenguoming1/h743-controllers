# Dependency provenance and licensing

Freerouting 2.1.0 is GPL-3.0. The adapted `src/app/freerouting/board/Trace.java` is derived from its tagged source; its modified trace-contact logic is distributed with source and the GPL text. `NativeGuardFactory.java`, `NativePadContactArea.java`, and `LocalRouter.java` integrate with that GPL engine. Preserve the GPL obligations when redistributing the combined program.

Eclipse ECJ 3.41.0 is the Java compiler. Its bundled `about.html` records EPL-2.0 terms. The included licensing notices come directly from the pinned official JARs. The Freerouting fat JAR also bundles dependencies under the licenses/notices retained here; do not replace those with a single blanket license assertion.

`vendor/provenance.json` gives official download URLs and exact SHA-256 digests. `bootstrap_dependencies.py` verifies the digest before installing either dependency in this directory. It downloads no board data and sends no board to any service. Binaries and the 344 MB tagged source archive are intentionally omitted from this checkpoint.

Python runtime dependency: Shapely 2.2.0 (BSD-3-Clause), installed from the official PyPI package registry. KiCad 10 must come from a verified official distribution and expose `pcbnew`; this package neither downloads nor substitutes a KiCad runtime.
