# Simulation Lab (v1.0.16)

Original bounded C++17/GLSL numerical fixture, MIT. Reuses Engine Scale Lab's device, buffers, command/fence, graphics pipeline and readback, not a new physics engine. No external solver code is vendored. Does not require float atomics, FP16, subgroup operations, ray query or a second queue.

## Models and preregistered comparisons

- Two-particle distance XPBD: hard 1.2 -> 1, soft h=0.1/compliance=0.01 -> 1.1. Colored in-place and Jacobi contribution/gather both run. Reset lambda once per substep, retain across three iterations. CPU FP64 formulas consume the identical rounded FP32 GPU inputs. GPU threshold 1e-5 model units; exact Python oracle separately uses 1e-12.
- Rope 32 nodes and cloth 8x8: stretch, diagonal-distance shear and two-edge distance-bending approximation. Three iterations per h=0.01 tick, eight ticks, gravity -0.1. Cloth compliance 0.01, rope 0.0001. One prescribed cloth anchor moves 0.002 per tick. CPU colored GS follows the identical reordered colors; Jacobi sums corrections with relaxation 1, no degree normalization. These are distinct algorithms, not convergence-equivalent. Gather scans all constraints for a small fixture, not a scalable adjacency implementation.
- Plane and sphere/capsule analytic projection: no self-collision, CCD or friction. Position threshold 5e-5, normal 5e-5, CPU/GPU residual difference 1e-4, lambda 5e-5, discrete penetration 1e-5, prescribed/fixed-point drift zero. Residual magnitude is recorded, not misrepresented as hard-constraint convergence for compliant cloth. These thresholds are in source before the expanded matrix's first execution; they are not widened on failure.
- Heightfield linear wave: velocity then height with central finite differences, h=0.01, c=0.5, unit XY domain. CFL c*h*sqrt(1/dx²+1/dy²)<=0.9. Separate source/destination SSBO stencil then publish. Fixed edge zeroes height/velocity; reflecting clamps neighbors; dissipative uses implicit damping 1/(1+0.1*h) plus 0.5 edge velocity. Height/velocity threshold 1e-5, normals 5e-5. 17x17 boundaries each run zero and overlapping two-impulse cases; extra single and dense 131-event cases, plus 9x9 resized grid. Events only apply on their specified tick. This is not Navier–Stokes, shallow-water, SPH or bidirectional particle/fluid coupling.

Total 144 numerical snapshots, 32 constraint reports and 52 draws. Bounds shared reduction has 64 lanes with neutral tail values and uniform barriers. Output records CPU/GPU positions, normals, bounds, constraint residuals/lambda and raw 65x49 RGBA/PPM. An independent Python checker recalculates errors and hashes rather than accepting the program's PASS string.

## Build and run

Requires reputable C++ compiler, Vulkan headers/loader, glslangValidator and spirv-val. Optional VULKAN_SDK_PREFIX points to an unpacked SDK's usr directory; GLSLANG and SPIRV_VAL may be absolute paths. No dependency is downloaded by these scripts.

    sh tests/fixtures/simulation_lab/build.sh /new/build-directory
    python3 tests/fixtures/simulation_lab/run_matrix.py /new/build-directory /new/run-directory --skill-root /path/to/skill
    VULKAN_SIM16_RUN_DIR=/new/run-directory pytest -q tests/test_simulation_lab.py

Choose the target via VK_DRIVER_FILES and VK_LAYER_PATH if required. A software implementation is an explicitly labeled correctness target, never a substitute for Android. Build and output paths must not exist. The runner has a 180-second timeout. Invalid step/CFL/index/capacity/color contracts are rejected in host tests, never tested by executing an intentionally invalid or deadlocking shader.

Build manifests bind the fixture source closure, executable and 15 SPIR-V modules to actual hashes. A release-quality run requires clean skill/tests revisions. Output hashes bind run records. Vulkan validation must be present and clean. Timestamp intervals are simulation, normal/bounds, draw and image copy; CPU command-record/submit/fence wall time is separate. Queries are read after the existing fence, without another query wait. Timestamp valid bits/period are recorded. The serialized baseline's timings include barriers and software/JIT overhead and imply no mobile speedup or energy result.

## Explicit unverified scope

Single queue with a synchronous fence per tick and consumer. Two render views do not advance simulation. Asynchronous multi-frame snapshot retirement, cross-queue transfer, shadow/motion/AS consumers are host contracts only, not actual concurrent GPU evidence. All-consumer completion and per-view previous presented pose are tested separately in simulation_host_contracts.py. Particle-to-wave event conversion is host-only, reusing the existing particle-pool architecture contract; no new GPU particle pool is claimed.

No Android/Adreno/Mali device, thermal trace, APK, mobile visual acceptance, live model inference, real host integration, transparent water integration, optional atomic/FP16/AS path, tetrahedral soft body or large-scale cloth performance is established by this fixture. Draw coverage proves only nonempty rendering; it is not a perceptual golden-image test. v1.0.15's paired evidence publication remains separately pending.
