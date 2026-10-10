#!/bin/sh
# Sourced by wrappers. All writeable application state stays in this workspace.
runtime_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export KICAD_CONFIG_HOME="$runtime_dir/config"
export XDG_CONFIG_HOME="$runtime_dir/config"
export XDG_CACHE_HOME="$runtime_dir/cache"
export XDG_DATA_HOME="$runtime_dir/data"
export KICAD10_SYMBOL_DIR="$runtime_dir/root/usr/share/kicad/symbols"
export KICAD10_FOOTPRINT_DIR="$runtime_dir/root/usr/share/kicad/footprints"
export KICAD10_TEMPLATE_DIR="$runtime_dir/root/usr/share/kicad/template"
export KICAD10_3DMODEL_DIR=/usr/share/kicad/3dmodels
runtime_lib="$runtime_dir/root/usr/lib/x86_64-linux-gnu"
runtime_loader="$runtime_lib/ld-linux-x86-64.so.2"
