#!/usr/bin/env python3
"""Run a bounded actual Vulkan matrix; no forged response/device evidence."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_manifest import digest,source_files
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('build',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--skill-root',type=Path,required=True);a=ap.parse_args()
    build=a.build.resolve();out=a.output.resolve();root=HERE.parents[2]
    if out.exists():raise ValueError('Refuse existing output directory')
    manifest=json.loads((build/'build-manifest.json').read_text())
    if manifest['sources']!=source_files(HERE):raise ValueError('Source changed since compilation')
    for path,sha in manifest['artifacts'].items():
        if digest(build/path)!=sha:raise ValueError('Compiled artifact changed')
    proc=subprocess.run([str(build/'simulation_lab'),str(build/'shaders'),str(out)],text=True,capture_output=True,timeout=180)
    if not out.exists():raise RuntimeError(proc.stderr or proc.stdout)
    (out/'stdout.log').write_text(proc.stdout);(out/'stderr.log').write_text(proc.stderr)
    (out/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    def git(folder,*args):return subprocess.check_output(['git','-C',str(folder),*args],text=True).strip()
    devices=[json.loads(line) for line in proc.stdout.splitlines() if line.startswith('{') and '"device"' in line]
    result=dict(schema=1,layer='VulkanIntegration',exit_code=proc.returncode,tests_sha=git(root,'rev-parse','HEAD'),tests_tree=git(root,'rev-parse','HEAD^{tree}'),tests_dirty=bool(git(root,'status','--porcelain')),skill_sha=git(a.skill_root,'rev-parse','HEAD'),skill_dirty=bool(git(a.skill_root,'status','--porcelain')),device=devices,software_vulkan=any(d.get("deviceType")==4 for d in devices),live='NOT_RUN',android='NOT_RUN',optional_async='NOT_IMPLEMENTED',files={p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    if proc.returncode:raise RuntimeError('Simulation failed: '+proc.stderr)
    subprocess.run([sys.executable,str(HERE/'verify_artifacts.py'),str(out)],check=True)
if __name__=='__main__':main()
