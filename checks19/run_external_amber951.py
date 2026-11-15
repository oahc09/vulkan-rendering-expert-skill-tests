#!/usr/bin/env python3
"""Replay the fixed locally rebuilt original Amber #951 before/after cohort."""
import argparse,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.external_amber95119 import run

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifact-root',required=True);p.add_argument('--out',required=True);p.add_argument('--timeout',type=int,default=30);a=p.parse_args()
 try:print(run(a.artifact_root,a.out,a.timeout)['status']);return 0
 except Exception as e:print('BLOCKED: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
