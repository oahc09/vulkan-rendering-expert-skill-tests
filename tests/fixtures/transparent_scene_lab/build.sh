#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT=${1:?usage: build.sh NEW_OUTPUT_DIR}
[ ! -e "$OUT" ] || { echo 'Refuse existing output directory' >&2; exit 1; }
mkdir -p "$OUT/shaders"
: "${CXX:=g++}" "${GLSLANG:=glslangValidator}" "${SPIRV_VAL:=spirv-val}"
# Reuse the Engine Scale Lab shaders required by its resource constructor.
for shader in "$HERE"/../engine_scale_lab/shaders/*.comp "$HERE"/../engine_scale_lab/shaders/*.vert "$HERE"/../engine_scale_lab/shaders/*.frag "$HERE"/shaders/*; do
 "$GLSLANG" -V --target-env vulkan1.2 -I"$HERE/../engine_scale_lab/shaders" "$shader" -o "$OUT/shaders/$(basename "$shader").spv"
 "$SPIRV_VAL" --target-env vulkan1.2 "$OUT/shaders/$(basename "$shader").spv"
done
if [ -n "${VULKAN_SDK_PREFIX:-}" ]; then
 "$CXX" -std=c++17 -O2 -Wall -Wextra -Wno-missing-field-initializers -I"$VULKAN_SDK_PREFIX/include" "$HERE/main.cpp" -L"$VULKAN_SDK_PREFIX/lib/x86_64-linux-gnu" -Wl,-rpath,"$VULKAN_SDK_PREFIX/lib/x86_64-linux-gnu" -l:libvulkan.so.1 -o "$OUT/transparent_scene_lab"
else
 "$CXX" -std=c++17 -O2 -Wall -Wextra -Wno-missing-field-initializers "$HERE/main.cpp" -l:libvulkan.so.1 -o "$OUT/transparent_scene_lab"
fi
