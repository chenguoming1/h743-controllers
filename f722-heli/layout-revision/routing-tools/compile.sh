#!/bin/sh
set -eu
cd "$(dirname "$0")"
java -jar vendor/ecj-3.41.0.jar -21 -nowarn -cp vendor/freerouting-2.1.0.jar -d build src/app/freerouting/board/*.java src/*.java
