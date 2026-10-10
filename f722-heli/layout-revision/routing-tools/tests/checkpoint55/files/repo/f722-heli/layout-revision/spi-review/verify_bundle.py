"""Verify this source-only packet and optionally its exact external board/parts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def blob_sha1(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path)
    parser.add_argument('--parts', type=Path)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'bundle-manifest.json').read_text())
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}
    require(actual == set(manifest['allowlist']), 'Unexpected or missing packet files')
    for entry in manifest['files']:
        path = ROOT / entry['path']
        require(not path.is_symlink(), 'Symlink in packet: ' + entry['path'])
        data = path.read_bytes()
        require(len(data) == entry['size_bytes'], 'Size mismatch: ' + entry['path'])
        require(sha256(data) == entry['sha256'], 'SHA-256 mismatch: ' + entry['path'])
    index = json.loads((ROOT / 'stock-source-index.json').read_text())
    for entry in index['files']:
        data = (ROOT / entry['packet_path']).read_bytes()
        require(blob_sha1(data) == entry['sha'], 'Upstream blob mismatch: ' + entry['path'])
    for key in ['firmware_license', 'target']:
        entry = index[key]
        require(blob_sha1((ROOT / entry['packet_path']).read_bytes()) == entry['git_blob_sha1'], key + ' blob mismatch')
    # Guard the constants transcribed into the arithmetic against pinned sources.
    sources = ROOT / 'firmware/src/main'
    constants = [('drivers/accgyro/accgyro_mpu.c', 'MPU_MAX_SPI_DETECT_CLK_HZ', 1000000),
                 ('drivers/accgyro/accgyro_spi_icm426xx.c', 'ICM426XX_MAX_SPI_CLK_HZ', 24000000),
                 ('drivers/flash.c', 'FLASH_MAX_SPI_INIT_CLK', 5000000),
                 ('drivers/flash_w25n01g.c', 'W25N01G_MAX_SPI_CLK_HZ', 104000000)]
    for path, name, value in constants:
        match = re.search(r'^#define\s+' + re.escape(name) + r'\s+(\d+)', (sources / path).read_text(), re.M)
        require(match is not None and int(match[1]) == value, 'Driver ceiling mismatch: ' + name)
    result = subprocess.run([sys.executable, str(ROOT / 'calculate_clocks.py')], check=True, capture_output=True, text=True)
    calculated = json.loads(result.stdout)
    require(calculated == json.loads((ROOT / 'clock-calculations.json').read_text()), 'Clock result differs from retained result')
    inventory = json.loads((ROOT / 'native-pad-identities.json').read_text())
    require(inventory['pcb_sha256'] == manifest['canonical69_pcb_sha256'], 'Inventory binding mismatch')
    if args.board:
        require(sha256(args.board.read_bytes()) == inventory['pcb_sha256'], 'Supplied board is outside the exact canonical69 binding')
    if args.parts:
        require(sha256(args.parts.read_bytes()) == index['authoritative_parts_sha256'], 'Supplied parts manifest is outside the review binding')
    print(json.dumps({'packet_files_verified': len(manifest['files']),
                      'firmware_blobs_verified': len(index['files']),
                      'clock_arithmetic_reproduced': True,
                      'canonical69_external_board_exact_match': True if args.board else None,
                      'authoritative_parts_exact_match': True if args.parts else None,
                      'scope': 'Source identities and nominal arithmetic only; no completed signal qualification'}, indent=2))

if __name__ == '__main__':
    main()
