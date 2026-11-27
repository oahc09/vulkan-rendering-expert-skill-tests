"""Bind compiled fixture artifacts to the complete local fixture source closure."""
import hashlib,json,subprocess,sys
from pathlib import Path

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def source_files(lab):
    root=lab.parents[2]
    paths=[p for p in lab.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    engine=lab.parent/'engine_scale_lab'
    paths += [engine/'main.cpp']+list((engine/'shaders').glob('*'))
    return {str(p.relative_to(root)):digest(p) for p in sorted(set(paths)) if p.is_file()}

def main():
    lab,build=map(lambda x:Path(x).resolve(),sys.argv[1:]);root=lab.parents[2]
    artifact=[build/'simulation_lab']+sorted((build/'shaders').glob('*.spv'))
    manifest=dict(schema=1,sources=source_files(lab),artifacts={str(p.relative_to(build)):digest(p) for p in artifact},tests_sha=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),tests_dirty=bool(subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True)))
    (build/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
