#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
package_root="$project_root/.tools/blender/root"
library_root="$package_root/usr/lib/aarch64-linux-gnu"

export LD_LIBRARY_PATH="$library_root:$library_root/blas:$library_root/lapack:$package_root/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export BLENDER_SYSTEM_SCRIPTS="$package_root/usr/share/blender/scripts"
export BLENDER_SYSTEM_DATAFILES="$package_root/usr/share/blender/datafiles"
export PYTHONPATH="$package_root/usr/lib/python3/dist-packages${PYTHONPATH:+:$PYTHONPATH}"

exec "$package_root/usr/bin/blender" "$@"
