"""Source/evidence integrity only, not a replay or proof of Vulkan correctness."""
import hashlib,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
pytestmark=pytest.mark.host_unit
def test_case_source_identity():
 d=json.loads((ROOT/'coverage/v1.0.19/transfer-case.json').read_text());p=ROOT/'cases19/transfer'
 before=(p/'baseline.c').read_text();after=before.replace('#define TRANSFER_FIX 0','#define TRANSFER_FIX 1')
 mutant=after.replace('.dstAccessMask=VK_ACCESS_TRANSFER_READ_BIT','.dstAccessMask=0')
 for key,text in [('before',before),('after',after),('mutant',mutant)]:
  assert hashlib.sha256(text.encode()).hexdigest()==d['cases'][key]['source_sha256']
 assert hashlib.sha256((p/'fix.patch').read_bytes()).hexdigest()==d['patch_sha256']
def test_case_claim_scope():
 d=json.loads((ROOT/'coverage/v1.0.19/transfer-case.json').read_text())
 assert 'deliberate fault injection' in d['provenance']
 assert d['runtime_identity']['device_type']==4
 assert d['cases']['after']['matching_words']==64
 assert d['cases']['mutant']['exit']==6
 assert d['cases']['after']['errors']==0
 assert 'SYNC-HAZARD-READ-AFTER-WRITE' in d['cases']['before']['message_ids']
