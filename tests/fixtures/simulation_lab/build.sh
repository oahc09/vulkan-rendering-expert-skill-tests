#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT=${1:?usage: build.sh NEW_OUTPUT_DIR}
[ ! -e "$OUT" ] || { echo 'Refuse existing output directory' >&2; exit 1; }
mkdir -p "$OUT/shaders"
: "${CXX:=g++}" "${GLSLANG:=glslangValidator}" "${SPIRV_VAL:=spirv-val}"
for shader in "$HERE"/../engine_scale_lab/shaders/*.comp "$HERE"/shaders/*.comp "$HERE"/shaders/*.vert "$HERE"/shaders/*.frag; do
 "$GLSLANG" -V --target-env vulkan1.2 -I"$HERE/../engine_scale_lab/shaders" -I"$HERE/shaders" "$shader" -o "$OUT/shaders/$(basename "$shader").spv"
 "$SPIRV_VAL" --target-env vulkan1.2 "$OUT/shaders/$(basename "$shader").spv"
done
if [ -n "${VULKAN_SDK_PREFIX:-}" ]; then
 "$CXX" -std=c++17 -O2 -Wall -Wextra -Wno-missing-field-initializers -I"$VULKAN_SDK_PREFIX/include" "$HERE/main.cpp" -L"$VULKAN_SDK_PREFIX/lib/x86_64-linux-gnu" -Wl,-rpath,"$VULKAN_SDK_PREFIX/lib/x86_64-linux-gnu" -l:libvulkan.so.1 -o "$OUT/simulation_lab"
else
 "$CXX" -std=c++17 -O2 -Wall -Wextra -Wno-missing-field-initializers "$HERE/main.cpp" -l:libvulkan.so.1 -o "$OUT/simulation_lab"
fi
python3 "$HERE/build_manifest.py" "$HERE" "$OUT"
