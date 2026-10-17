#!/usr/bin/env python3
"""Standard-library integration tests for the scanner root-path contract."""
import argparse,json,pathlib,subprocess,sys,tempfile
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=pathlib.Path,required=True)
    p.add_argument('--registry-dir',type=pathlib.Path,required=True)
    p.add_argument('--vk-xml',type=pathlib.Path,required=True)
    a=p.parse_args();script=pathlib.Path(__file__).with_name('scan_registry.py');root=a.root.resolve()
    with tempfile.TemporaryDirectory() as td:
     temp=pathlib.Path(td)
     def run(candidate,label):
      out=temp/(label+'.json')
      r=subprocess.run([sys.executable,str(script),'--root',str(candidate),'--registry-dir',str(a.registry_dir),'--vk-xml',str(a.vk_xml),'--output',str(out)],capture_output=True,text=True)
      return r,out
     result,out=run(root,'real')
     assert result.returncode==0,result.stderr
     data=json.loads(out.read_text());expected=len(list((root/'references/03_api_manual').rglob('*.md')))
     assert expected>0 and data['counts']['files']==expected
     assert all(x.startswith('references/03_api_manual/') for x in data['input_sha256'])
     print(f'PASS real root: {expected} Markdown files, paths relative to exact Skill root')
     result,out=run(root.parent,'wrong_parent')
     assert result.returncode!=0 and not out.exists()
     assert 'exact Skill repository root' in result.stderr
     print('PASS wrong parent root: nonzero exit, no output artifact')
     empty=temp/'empty_skill';(empty/'references/03_api_manual').mkdir(parents=True)
     result,out=run(empty,'empty')
     assert result.returncode!=0 and not out.exists()
     assert 'refusing an empty audit' in result.stderr
     print('PASS empty manual directory: nonzero exit, no output artifact')

if __name__ == "__main__":
    main()
