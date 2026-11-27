#!/usr/bin/env python3
import argparse,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tools.external_related19 import run
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--artifact-root',required=True);p.add_argument('--out',required=True);p.add_argument('--run-id');a=p.parse_args()
 try:print(run(a.artifact_root,a.out,a.run_id)['status'])
 except Exception as e:print('BLOCKED: '+str(e),file=sys.stderr);sys.exit(2)
