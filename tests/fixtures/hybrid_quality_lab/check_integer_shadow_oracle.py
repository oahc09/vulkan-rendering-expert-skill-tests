"""Independent business oracle for the exact integer-grid fixture. No external dependencies."""
import argparse
from math import floor, sin
from pathlib import Path

W, H = 65, 49
JITTER = [0, 0, 0, .25, -.25, 0, 0, .125, -.125, .25, -.25, 0]


def edge(ndc, size):
    return floor((ndc + 1) * size / 2 + .5)


def expected(frame):
    light = (-.55 if frame >= 6 else -.35) + JITTER[frame] * 2 / W
    tick = frame if frame >= 7 else 0
    solids = (
        (-.25, 0, .18, .25, .6, False),
        (.2 + .12 * sin(tick * .3), .15, .22, .4, .35, True),
        (.82, -.25, .12, .2, .2, False),
    )
    depth = bytearray([255] * (W * H))
    for cx, cy, rx, ry, z, alpha in solids:
        cx += light * (.8 - z)
        x0, x1, y0, y1 = edge(cx-rx,W), edge(cx+rx,W), edge(cy-ry,H), edge(cy+ry,H)
        if x1 <= x0 or y1 <= y0:
            raise ValueError("degenerate authored blocker")
        for y in range(max(y0,0), min(y1,H)):
            for x in range(max(x0,0), min(x1,W)):
                # floor division is exact at the rational center. Opaque iff in
                # the first half of a seven-period stripe (the midpoint is included).
                u = (x-x0) * 2 + 1
                period = (x1-x0) * 2
                if alpha and (u*7 - (u*7//period)*period)*2 > period:
                    continue
                i = y*W+x
                depth[i] = min(depth[i], floor(z*255+.5))
    return depth


FRAME_SUFFIXES = ("shadow-depth.pgm", "receiver-depth.pgm", "raw.pgm",
                  "temporal.pgm", "filtered.pgm", "history-weight.pgm",
                  "raw-color.ppm", "filtered-color.ppm")


def compare_previews(first, second):
    names = {f"frame-{frame}-{suffix}" for frame in range(12) for suffix in FRAME_SUFFIXES}
    for directory in (first, second):
        present = {p.name for p in directory.glob("frame-*") if p.suffix in (".ppm", ".pgm")}
        if present != names:
            raise ValueError(f"unexpected preview inventory in {directory}")
    return sum((first / f).read_bytes() != (second / f).read_bytes() for f in names)


def check(source):
    mismatch = 0
    for f in range(12):
        p = source / f"frame-{f}-shadow-depth.pgm"
        a, b, c, data = p.read_bytes().split(b"\n",3)
        if (a,b,c,len(data)) != (b"P5", b"65 49", b"255",65*49):
            raise ValueError(f"unexpected PGM header {p}")
        ref = expected(f)
        if len(set(ref)) != 4:
            raise ValueError("reference does not contain all 3 caster depths and clear")
        mismatch += sum(x!=y for x,y in zip(data,ref))
    return mismatch


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("root",type=Path)
    parser.add_argument("--second-driver", type=Path)
    args=parser.parse_args()
    mismatches=check(args.root)
    print(f"compared_texels={12*W*H} mismatches={mismatches}")
    if args.second_driver:
        errors = check(args.second_driver)
        different = compare_previews(args.root, args.second_driver)
        print(f"second_driver_texels={12*W*H} mismatches={errors} differing_previews={different}/96")
        mismatches += errors + different
    raise SystemExit(1 if mismatches else 0)
