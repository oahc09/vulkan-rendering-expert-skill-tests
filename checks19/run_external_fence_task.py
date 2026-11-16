#!/usr/bin/env python3
"""Run pinned upstream FencePool class at a HOST Vulkan-call test-double boundary."""
import argparse
import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.external_fence19 import run

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source-repo',required=True)
 p.add_argument('--headers',required=True,help='official Vulkan include root')
 p.add_argument('--out',required=True)
 p.add_argument('--run-id')
 a=p.parse_args()
 try:
  r=run(a.source_repo,a.headers,a.out,a.run_id)
  print(r['status']);return 0
 except Exception as e:
  print('BLOCKED: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
