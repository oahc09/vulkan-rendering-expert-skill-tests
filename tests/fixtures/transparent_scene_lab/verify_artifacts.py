#!/usr/bin/env python3
"""Reopen actual pixels; perturb an image and ensure the oracle rejects it."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

def rgba(p):
    raw=p.read_bytes()
    if len(raw)!=65*49*16:raise ValueError('wrong dimensions')
    a=struct.unpack('<'+str(65*49*4)+'f',raw)
    if not all(map(math.isfinite,a)):raise ValueError('nonfinite pixels')
    return a

def center_check(a,expected,tolerance):
    i=(24*65+32)*4
    if max(abs(a[i+c]-expected[c]) for c in range(4))>tolerance:raise ValueError('center oracle mismatch')

def verify(root):
    repo=Path(__file__).resolve().parents[3]
    def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def require_equal(a,b):
        if a!=b:raise ValueError('hash inventory mismatch')
    sources=json.loads((root/'source-manifest.json').read_text())
    if not sources:raise ValueError('empty source inventory')
    for name,sha in sources.items():
        path=(repo/name).resolve()
        if not path.is_relative_to(repo):raise ValueError('source outside repository')
        require_equal(digest(path),sha)
    manifest=root/'artifact-manifest.json'
    if manifest.exists():
        recorded=json.loads(manifest.read_text())
        actual={str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file() and p!=manifest}
        require_equal(recorded,actual)
        corrupted=dict(recorded);corrupted[next(iter(corrupted))]='0'*64
        try:require_equal(corrupted,actual)
        except ValueError:pass
        else:raise ValueError('hash mutation escaped')
    tested=0
    for mode in ['auto','fallback']:
        log=(root/(mode+'.log')).read_text()
        if 'VALIDATION:' in log or '"integration":"PASS"' not in log:raise ValueError('validation/run diagnostic')
        rows=[json.loads(s) for s in (root/mode/'frames.jsonl').read_text().splitlines()]
        for fmt,tol in [(37,.009),(97,.003),(109,1e-5)]:
            if any(r.get('format')==fmt and r.get('status')=='SKIPPED_FORMAT_CAPABILITY' for r in rows):continue
            for frame,expected in [(0,[.5,0,.25,.75]),(1,[.25,0,.5,.75])]:
                a=rgba(root/mode/f'format-{fmt}-frame-{frame}.rgba32f');center_check(a,expected,tol);tested+=1
                corrupt=list(a);corrupt[(24*65+32)*4]+=.1
                try:center_check(corrupt,expected,tol)
                except ValueError:pass
                else:raise ValueError('negative mutation escaped')
        # Device may skip high precision; only claim executed artifacts.
        effects=root/mode/'effects-8.rgba32f'
        if effects.exists():
            a,b=rgba(effects),rgba(root/mode/'effects-16.rgba32f')
            if max(abs(x-y) for x,y in zip(a,b))>2e-6:raise ValueError('step-size invariance')
            # x=7 shifts onto the foreground wall (x=10); must use unshifted black.
            # Particle lies inside volume: integrate front [2,3], particle, back [3,6].
            tf,tb=math.exp(-.35),math.exp(-1.05)
            expected=[(.2+.1*c)*(1-tf)+tf*(.7*.2+.8*(.2+.1*c)*(1-tb)) for c in range(3)]
            i=(24*65+7)*4
            if max(abs(a[i+c]-expected[c]) for c in range(3))>2e-6:raise ValueError('silhouette fallback / segment order')
            wrong_shift=[expected[c]+tf*.8*tb*[.15,.2,.25][c] for c in range(3)]
            wrong_order=[.7*.2+.8*(.2+.1*c)*(1-tf*tb) for c in range(3)]
            for bad in [wrong_shift,wrong_order]:
                if max(abs(a[i+c]-bad[c]) for c in range(3))<.001:raise ValueError('effect negative not discriminating')

        for p in (root/mode).glob('*.rgba32f'):rgba(p)
    if not tested:raise ValueError('no sorted blend path executed')
    return {'pixel_oracle_checks':tested,'mutation_rejections':tested,'status':'PASS'}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1]))))
