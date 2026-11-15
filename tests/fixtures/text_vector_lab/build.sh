#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT=$1
if [ -e "$OUT" ]; then echo 'Refuse existing output directory' >&2; exit 1; fi
mkdir -p "$OUT/shaders"
: "${CXX:=g++}" "${GLSLANG:=glslangValidator}" "${SPIRV_VAL:=spirv-val}"
for shader in "$HERE"/../engine_scale_lab/shaders/*.comp "$HERE"/../engine_scale_lab/shaders/*.vert "$HERE"/../engine_scale_lab/shaders/*.frag "$HERE"/fullscreen.vert "$HERE"/coverage.frag; do
 "$GLSLANG" -V --target-env vulkan1.2 -I"$HERE/../engine_scale_lab/shaders" "$shader" -o "$OUT/shaders/$(basename "$shader").spv"
 "$SPIRV_VAL" --target-env vulkan1.2 "$OUT/shaders/$(basename "$shader").spv"
done
# Official headers may be extracted rootlessly. Link the installed loader ABI.
"$CXX" -std=c++17 -O2 -Wall -Wextra -Wno-missing-field-initializers ${VULKAN_SDK_PREFIX:+-I"$VULKAN_SDK_PREFIX/include"} "$HERE/main.cpp" -l:libvulkan.so.1 -o "$OUT/text_vector_lab"
