import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import prose_generation19 as g
pytestmark=pytest.mark.candidate19
def fixture(root):
 for n in g.REQUIRED:
  f=root/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'')
 (root/'specattribs.adoc').write_text(''.join(':'+x+':\n' for x in g.ATTRIBUTES)+':SPECREVISION: 1.4.368\n')
 (root/'api/structs/VkMemoryDedicatedRequirements.adoc').write_text('[[VkMemoryDedicatedRequirements]]\nVkBool32           prefersDedicatedAllocation;\nVkBool32           requiresDedicatedAllocation;\n')
 return root
@pytest.mark.parametrize('kind',['missing','symbol','version','extension','marker','pyc','symlink'])
def test_mutants(tmp_path,kind):
 root=fixture(tmp_path/'gen');assert g.validate(root)
 if kind=='missing':(root/'apimap.py').unlink()
 elif kind=='symbol':(root/'api/structs/VkMemoryDedicatedRequirements.adoc').write_text('fake success')
 elif kind=='version':(root/'specattribs.adoc').write_text(':SPECREVISION: 1.4.309\n')
 elif kind=='extension':
  with (root/'specattribs.adoc').open('a') as f:f.write(':VK_EXT_fake:\n')
 elif kind=='marker':(root/'api/timeMarker').write_text('nonempty')
 elif kind=='pyc':(root/'extra.pyc').write_bytes(b'fake')
 else:(root/'link').symlink_to(root/'apimap.py')
 with pytest.raises(ValueError):g.validate(root)
def test_reproducible_and_changed_tag(tmp_path):
 a=fixture(tmp_path/'a');b=fixture(tmp_path/'b');assert g.compare(g.validate(a),g.validate(b))
 (b/'validity/structs/VkMemoryDedicatedRequirements.adoc').write_text('tag::forged[]')
 with pytest.raises(ValueError):g.compare(g.validate(a),g.validate(b))
def test_include_not_expanded():
 files={'a.adoc':{'raw':b'include::{generated}/api/A.adoc[tag=x]\ninclude::{generated}/missing.adoc[]\nifdef::EXT[]\ninclude::https://remote/x[]\nendif::EXT[]\n'}}
 rows=g.include_observations(files,{'api/A.adoc':'hash'});assert rows[0]['status']=='FILE_EXISTS_NOT_EXPANDED' and rows[0]['options_raw']=='tag=x';assert rows[1]['status']=='MISSING_OR_UNRESOLVED_NOT_PROVEN_ACTIVE';assert all(x['conditions']=='NOT_EVALUATED' for x in rows)
def test_success_label_not_inventory():
 with pytest.raises(ValueError):g.compare({'status':'PASS'},{'status':'PASS','missing':'file'})
