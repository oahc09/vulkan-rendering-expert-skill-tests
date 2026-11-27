# transparent-lab-linear-diagonal-v1

Original MIT synthetic ASCII PLY 1.0 only. Header order/types match generate.py;
unknown profiles and alternative producer conventions are rejected, not guessed.
Seed 115 (Python MT19937) and exact generated asset bytes are recorded per run.

Position x/y in orthographic clip coordinates, z in normalized forward depth
[.01,1]. For the effects test only, z*10 is world distance. Axis scales are positive
linear standard deviations, not logarithms; covariance is diag(scale²). Identity
rotation is implicit; arbitrary quaternion/SH input is unsupported. Radius is 3σ.
RGB are linear display-independent synthetic radiance values [0,1], not sRGB or
SH/DC coefficients; do not light them again. Opacity is probability [0,1], not logit.

Fields: x y z scale_x scale_y scale_z red green blue opacity (float), set_id
local_id generation (uint). Stable identity tuple is unique. Binary export is
little-endian 64 bytes/instance: vec4 center, vec4 radii, vec4 straight RGBA,
uvec4(set,local,generation,gaussian=1). Orthographic projected x/y radii are 3σ;
z scale is validated but does not enter this restricted projection. Sorted by
(-z,set_id,local_id,generation). No claimed compatibility with arbitrary training
PLY, SPZ, glTF or Mobile-4DGS model compression. No external asset license implied.
