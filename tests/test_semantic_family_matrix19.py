"""Semantic delivery routes cannot silently promote whole-domain acceptance."""
import json
from pathlib import Path

def test_host_semantic_routes_exist_and_remain_bounded():
    root=Path(__file__).resolve().parents[1]
    rows=json.loads((root/'coverage/v1.0.19/domains.json').read_text())
    seen=set()
    for row in rows:
        for contract in row.get('host_semantic_contracts',[]):
            seen.add(row['id'])
            assert contract['domain_complete'] is False
            assert contract['semantic_completion']=='UNKNOWN_NOT_INFERRED'
            assert contract['evidence_kind']=='HOST_CALLER_FACTS_NOT_GPU'
            assert row['status']=='PARTIAL_BOUNDED'
            for key in ('document','entry','rules'):
                assert (root/contract[key]).is_file(),contract[key]
            assert (root/'coverage/v1.0.19'/contract['evidence']).is_file()
    assert {'VK05','VK06','VK07'}<=seen
