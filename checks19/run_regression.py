#!/usr/bin/env python3
"""Current exact-pair regression; historical version assertions stay immutable.
Default runs every test except nine explicit historical-pair nodes. Optional tool
and Live tests retain native skip/opt-in behavior; skip never means acceptance.
"""
import argparse, ast, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HISTORICAL={
 'test_core17_pair.py::test_exact_skill_and_base_contract':'core17-candidate-contract.json',
 'test_core17_pair.py::test_core17_version_and_preserved_routing':'core17-candidate-contract.json',
 'test_core17_pair.py::test_core17_reproducible_package_and_unchanged_knowledge_budget':'core17-candidate-contract.json',
 'test_text18_package_pair.py::test_exact_skill_and_base_contract':'text18-candidate-contract.json',
 'test_text18_package_pair.py::test_text18_version_and_preserved_routing':'text18-candidate-contract.json',
 'test_text18_package_pair.py::test_text18_reproducible_package_and_unchanged_knowledge_budget':'text18-candidate-contract.json',
 'test_v1_0_18_contracts.py::test_candidate_skill_pin_and_on_demand_anchors':'text18-candidate-contract.json',
 'test_v1_0_8_project_diagnosis.py::test_current_version_and_preserved_project_diagnosis_routing':'release-contract.json',
 'test_v1_0_9_regression.py::test_release_version_and_manifest_budget':'release-contract.json',
}
def exclusions():
 for node,contract in HISTORICAL.items():
  file,name=node.split('::')
  tree=ast.parse((ROOT/'tests'/file).read_text())
  if name not in {n.name for n in tree.body if isinstance(n,ast.FunctionDef)}:raise ValueError('historical node no longer exists: '+node)
  c=json.loads((ROOT/contract).read_text())
  if c.get('expected_version',c.get('candidate_version')) not in ('1.0.16','1.0.17-reconstructed-tests','1.0.18'):raise ValueError('not a historical version contract')
 return ['--deselect='+node for node in HISTORICAL]
def main():
 p=argparse.ArgumentParser();p.add_argument('--skill',type=Path,required=True);p.add_argument('--junit',type=Path,required=True);p.add_argument('--pair',choices=('historical-v1.0.19','current-v1.0.20'),default='historical-v1.0.19');a=p.parse_args()
 subprocess.run([sys.executable,str(ROOT/'checks19/check_pair.py'),'--skill',str(a.skill.resolve()),'--pair',a.pair],check=True)
 args=exclusions()
 print(json.dumps({'historical_pair_nodes':HISTORICAL,'note':'run separately against immutable historical cohorts; never counted as current passes'},indent=2),flush=True)
 return subprocess.run([sys.executable,'-m','pytest','-q','-ra','tests',*args,'--junitxml='+str(a.junit.resolve())],cwd=ROOT,env=dict(os.environ,VULKAN_SKILL_ROOT=str(a.skill.resolve()),VULKAN_REGRESSION_PAIR=a.pair)).returncode
if __name__=='__main__':raise SystemExit(main())
