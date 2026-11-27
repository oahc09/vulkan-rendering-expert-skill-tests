import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import reference_font_repair19 as r
pytestmark=pytest.mark.candidate19

def setup(tmp_path):
 html=tmp_path/'man/html';html.mkdir(parents=True)
 fonts=tmp_path/'katex/fonts';fonts.mkdir(parents=True)
 before=b''
 for n in range(9):
  name='KaTeX_Test'+str(n)+'.woff2';(fonts/name).write_bytes(b'wOF2fixture')
  before+=b'<link rel="preload" as="font" href="../katex/fonts/'+name.encode()+b'">'
 return html,before,before.replace(r.OLD,r.NEW)
def test_positive(tmp_path):
 d,b,a=setup(tmp_path);assert len(r.page(b,a,d))==9
@pytest.mark.parametrize('kind',['other-body','old-href','missing-font','fake-font','symlink-font','missing-preload'])
def test_mutations(tmp_path,kind):
 d,b,a=setup(tmp_path);assert len(r.page(b,a,d))==9
 f=tmp_path/'katex/fonts/KaTeX_Test0.woff2'
 if kind=='other-body':a+=b'changed'
 elif kind=='old-href':a=b
 elif kind=='missing-font':f.unlink()
 elif kind=='fake-font':f.write_bytes(b'not-font')
 elif kind=='symlink-font':f.unlink();f.symlink_to('KaTeX_Test1.woff2')
 else:a=a.replace(b'<link',b'<span',1)
 with pytest.raises(ValueError):r.page(b,a,d)
def test_patch_wrong_preimage():
 with pytest.raises(ValueError):r.patch(b'no preimage')

def test_external_preload_unchanged(tmp_path):
 d,b,a=setup(tmp_path);external=b'<link rel="preload" as="font" href="https://example.test/FontAwesome.woff2">';b+=external;a+=external
 assert len(r.page(b,a,d))==9
 with pytest.raises(ValueError):r.page(b,a.replace(b'FontAwesome',b'Other'),d)

def test_real_positive_then_corruption():
 import os
 root=os.environ.get('VULKAN_REFERENCE_FONT_REPAIR19_BUILD')
 baseline=os.environ.get('VULKAN_REFERENCE_FONT_REPAIR19_BASELINE')
 if not root or not baseline:pytest.skip('explicit existing actual build and baseline required')
 d=Path(root)/'source/gen/out/man/html';before=(Path(baseline)/'source/gen/out/man/html/VkMemoryDedicatedRequirements.html').read_bytes();after=(d/'VkMemoryDedicatedRequirements.html').read_bytes()
 assert len(r.page(before,after,d))==9
 with pytest.raises(ValueError):r.page(before,after.replace(r.NEW,r.OLD,1),d)
 with pytest.raises(ValueError):r.page(before,after.replace(b'fontawesome',b'wrongfont',1),d)

@pytest.mark.parametrize('mutation',['target','scope','missing','extra'])
def test_fixed_commands(mutation):
 steps=[{'label':n,'argv':v}for n,v in r.commands(Path('/fixed/build'),Path('/fixed/runtime'))]
 r.verify_commands(steps,Path('/fixed/build'),Path('/fixed/runtime'))
 if mutation=='target':steps[-1]['argv'][-1]='html'
 elif mutation=='scope':steps[-1]['argv'][5]='core'
 elif mutation=='missing':steps.pop()
 else:steps.append(dict(steps[0]))
 with pytest.raises(ValueError):r.verify_commands(steps,Path('/fixed/build'),Path('/fixed/runtime'))
