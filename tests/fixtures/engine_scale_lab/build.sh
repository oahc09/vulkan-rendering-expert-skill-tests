#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT=${1:-"$HERE/build"}
mkdir -p "$OUT/shaders"
: "${CXX:=g++}"
: "${GLSLANG:=glslangValidator}"
: "${SPIRV_VAL:=spirv-val}"
for shader in "$HERE"/shaders/*.comp "$HERE"/shaders/*.vert "$HERE"/shaders/*.frag; do
 "$GLSLANG" -V --target-env vulkan1.2 -I"$HERE/shaders" "$shader" -o "$OUT/shaders/$(basename "$shader").spv"
 "$SPIRV_VAL" --target-env vulkan1.2 "$OUT/shaders/$(basename "$shader").spv"
done
# Optional rootless SDK prefix; never download or modify the system from this script.
if [ -n "${VULKAN_SDK_PREFIX:-}" ]; then
 "$CXX" -std=c++17 -O2 -Wall -Wextra -Wno-missing-field-initializers -I"$VULKAN_SDK_PREFIX/include" "$HERE/main.cpp" -L"$VULKAN_SDK_PREFIX/lib/x86_64-linux-gnu" -Wl,-rpath,"$VULKAN_SDK_PREFIX/lib/x86_64-linux-gnu" -lvulkan -o "$OUT/engine_scale_lab"
else
 "$CXX" -std=c++17 -O2 -Wall -Wextra -Wno-missing-field-initializers "$HERE/main.cpp" -lvulkan -o "$OUT/engine_scale_lab"
fi
"$CXX" -std=c++17 -O2 -Wall -Wextra "$HERE/host_contracts.cpp" -o "$OUT/host_contracts"
python3 "$HERE/verify_spirv.py" "$OUT" > "$OUT/shader-manifest.json"
