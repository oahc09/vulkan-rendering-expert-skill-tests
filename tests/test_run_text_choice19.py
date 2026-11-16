import importlib.util,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('text_entry',ROOT/'checks19/run_text_choice.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
pytestmark=pytest.mark.candidate19
def test_inventory_escape(tmp_path):
 outside=tmp_path/'outside';outside.write_text('x');out=tmp_path/'out';out.mkdir();(out/'escape').symlink_to(outside)
 with pytest.raises(ValueError,match='escape'):entry.inventory(out)
def test_inventory_nested_report_included(tmp_path):
 (tmp_path/'child').mkdir();(tmp_path/'child/report.json').write_text('{}');(tmp_path/'report.json').write_text('{}')
 assert list(entry.inventory(tmp_path))==['child/report.json']
def test_wrong_source_no_execution(tmp_path,monkeypatch):
 args=['entry']
 for k in ('tools','include','loader','icd','libdir','layerdir','skill-root','variable-font','msdf-source'):args+=['--'+k,str(tmp_path)]
 args+=['--output',str(tmp_path/'out'),'--expected-tests-head','a'*40,'--expected-skill-head','b'*40]
 monkeypatch.setattr(sys,'argv',args);monkeypatch.setattr(entry,'git',lambda *args:'bad')
 assert entry.main()==2
 import json
 report=json.loads((tmp_path/'out/report.json').read_text());assert report['status']=='BLOCKED' and report['steps']==[]
def test_reused_output_refused(tmp_path,monkeypatch):
 args=['entry']
 for k in ('tools','include','loader','icd','libdir','layerdir','skill-root','variable-font','msdf-source','output'):args+=['--'+k,str(tmp_path)]
 args+=['--expected-tests-head','a'*40,'--expected-skill-head','b'*40];monkeypatch.setattr(sys,'argv',args)
 with pytest.raises(FileExistsError):entry.main()
