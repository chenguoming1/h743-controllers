"""Run the unchanged upstream timing calculation on the host, without flashing hardware."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "stock-ba6c7e3"
compiler = shutil.which("cc")
if not compiler:
    raise SystemExit("A C compiler named cc is required.")
with tempfile.TemporaryDirectory(prefix="f722-i2c-review-") as temporary:
    executable = Path(temporary) / "timing_probe"
    subprocess.run([
        compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-I", str(SOURCE),
        str(SOURCE / "src/main/drivers/bus_i2c_timing.c"),
        str(SOURCE / "timing_probe.c"), "-o", str(executable),
    ], check=True)
    result = subprocess.run([str(executable)], check=True, capture_output=True, text=True)
    print(result.stdout, end="")
