#!/usr/bin/env python3
"""Original deterministic synthetic orthographic diagonal-covariance splats, MIT."""
import argparse
import json
import math
from pathlib import Path
import random
import struct

PROFILE = "transparent-lab-linear-diagonal-v1"
FIELDS = "x y z scale_x scale_y scale_z red green blue opacity set_id local_id generation"

def generate(count=16, footprint=0.15, seed=115):
    if not 1 <= count <= 128 or not math.isfinite(footprint) or not 0 < footprint <= 2:
        raise ValueError("capacity=128; finite footprint in (0,2]")
    rng = random.Random(seed)
    return [[rng.uniform(-1.15, 1.15), rng.uniform(-.8, .8), rng.uniform(.3, .9),
             footprint / 3, footprint / 6, .01,
             float(i % 2), .2, float(1-i % 2), .15, i % 2 + 1, i // 2, 1]
            for i in range(count)]

def encode(rows):
    return "\n".join(["ply", "format ascii 1.0", "comment profile " + PROFILE,
                      "element vertex " + str(len(rows))] +
                     ["property " + ("uint" if i >= 10 else "float") + " " + n
                      for i, n in enumerate(FIELDS.split())] + ["end_header"] +
                     [" ".join(map(str, r)) for r in rows]) + "\n"

def decode(text):
    lines = text.splitlines()
    header, body = lines[:lines.index("end_header")], lines[lines.index("end_header")+1:]
    if header[:3] != ["ply", "format ascii 1.0", "comment profile " + PROFILE]:
        raise ValueError("unknown PLY profile")
    count = int(header[3].removeprefix("element vertex "))
    expected = ["property " + ("uint" if i >= 10 else "float") + " " + n
                for i, n in enumerate(FIELDS.split())]
    if header[4:] != expected or not 1 <= count <= 128 or len(body) != count:
        raise ValueError("schema/count/capacity")
    rows = []
    ids = set()
    for line in body:
        row = list(map(float, line.split()))
        if len(row) != 13 or not all(map(math.isfinite, row)) or any(v <= 0 for v in row[3:6]):
            raise ValueError("invalid covariance/nonfinite")
        if not 0 <= row[9] <= 1 or any(v < 0 or v > 1 for v in row[6:9]) or not .01 <= row[2] <= 1:
            raise ValueError("unsupported domain")
        if any(v < 0 or v != int(v) or v > 16777216 for v in row[10:]) or tuple(row[10:]) in ids:
            raise ValueError("invalid/duplicate stable identity")
        ids.add(tuple(row[10:]));rows.append(row)
    return rows

def binary(rows):
    result = b""
    for r in sorted(rows, key=lambda r: (-r[2], r[10], r[11], r[12])):
        result += struct.pack("<12f4I", *r[:3], 0, r[3]*3, r[4]*3, 0, 0,
                              *r[6:10], *map(int, r[10:]), 1)
    return result

def main():
    p = argparse.ArgumentParser();p.add_argument("--out", required=True, type=Path)
    p.add_argument("--count", type=int, default=16);p.add_argument("--footprint", type=float, default=.15)
    a = p.parse_args();a.out.mkdir(parents=True, exist_ok=False)
    text = encode(generate(a.count, a.footprint));rows = decode(text)
    (a.out/"synthetic.ply").write_text(text);(a.out/"synthetic.bin").write_bytes(binary(rows))
    failures = []
    for label, bad in [("profile",text.replace(PROFILE,"unknown")),("nan",text.replace("0.01", "nan",1)),("negative_covariance",text.replace("0.01", "-0.01",1)),("overflow",text.replace("element vertex 16","element vertex 129"))]:
        if label == "overflow" and a.count != 16: continue
        try: decode(bad)
        except ValueError: failures.append(label)
        else: raise AssertionError(label)
    (a.out/"generator.json").write_text(json.dumps({"profile":PROFILE,"count":len(rows),"footprint":a.footprint,"seed":115,"negative_rejections":failures},indent=2)+"\n")
if __name__ == "__main__":main()
