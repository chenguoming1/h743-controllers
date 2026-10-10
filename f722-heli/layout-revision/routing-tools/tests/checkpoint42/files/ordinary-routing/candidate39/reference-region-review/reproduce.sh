#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/../../.."
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=python-deps python \
  ordinary-routing/candidate39/reference-region-review/classify_reference_delta.py \
  --before-board ordinary-routing/candidate38/f722-heli.kicad_pcb \
  --after-board ordinary-routing/candidate39/f722-heli.kicad_pcb \
  --before-snapshot checkpoint44-review/snapshot \
  --after-snapshot ordinary-routing/candidate39/reference-snapshot \
  --comparison ordinary-routing/candidate39/reference-comparison-to38.json \
  --expected-before-sha256 95bb984bf046fef2d96c6e59d9e00696f504d35f89e3340fdf076cd7c9249c9f \
  --expected-after-sha256 246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7
