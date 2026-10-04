#!/bin/sh
export KICAD_CONFIG_HOME=/tmp/controller-r3-kicad
export XDG_CACHE_HOME=/tmp/controller-r3-cache
export XDG_DATA_HOME=/tmp/controller-r3-data
# Rehydrate standard footprint lookup after an ephemeral runtime restart.
mkdir -p "$KICAD_CONFIG_HOME/9.0"
if [ ! -f "$KICAD_CONFIG_HOME/9.0/fp-lib-table" ]; then
    cp /usr/share/kicad/template/fp-lib-table "$KICAD_CONFIG_HOME/9.0/fp-lib-table"
fi
exec kicad-cli "$@"
