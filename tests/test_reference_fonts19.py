import importlib.util,json,os
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fontprobe',ROOT/'checks19/probe_reference_fonts19.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
pytestmark=pytest.mark.candidate19

def test_nine_preloads_and_wrong_depth(tmp_path):
 p=tmp_path/'page.html';p.write_text(''.join('<link rel="preload" as="font" href="../katex/fonts/KaTeX_'+str(i)+'.woff2">' for i in range(9)))
 assert len(h.inspect(p,'../katex')['hrefs'])==9
 with pytest.raises(ValueError):h.inspect(p,'../../katex')
 p.write_text(p.read_text().replace('KaTeX_8','KaTeX_7'))
 with pytest.raises(ValueError):h.inspect(p,'../katex')

def test_actual_patch_probe_optin():
 root=os.environ.get('VULKAN_REFERENCE_FONTS19_RUN')
 if not root:pytest.skip('actual isolated reference-font patch probe not supplied')
 root=Path(root);r=json.loads((root/'report.json').read_text());assert r['status']=='SCOPED_PRELOAD_FIX_AND_REVERSION_VERIFIED'
 assert [s['label'] for s in r['steps']]==['patched-reference','patched-specification','reverted-reference']
 assert all(s['returncode']==0 and s['group_cleanup']['group_gone'] for s in r['steps'])
 assert len(r['patched_reference']['existing'])==9 and r['reverted_reference']['existing']==[]
 assert r['baseline']['reference']['html_sha256']==r['reverted_reference']['html_sha256']
 assert r['baseline']['specification']['html_sha256']==r['patched_specification']['html_sha256']
 for f,digest in r['artifacts'].items():assert h.p.sha((root/f).read_bytes())==digest
 assert (root/'baseline-reference.html').read_bytes()==(root/'reverted-reference.html').read_bytes()
 assert (root/'patched-reference.html').read_bytes()==(root/'baseline-reference.html').read_bytes().replace(b'href="../katex/fonts/',b'href="../../katex/fonts/')
 assert (root/'baseline-specification.html').read_bytes()==(root/'patched-specification.html').read_bytes()
