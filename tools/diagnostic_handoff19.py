"""Portable read-only triage package: hashes bind bytes, not truth or re-execution."""
import hashlib,json,pathlib,re,uuid
from html.parser import HTMLParser
CASE_KINDS={
 'transfer':{'before':'injected defect','after':'minimal patch verified','mutant':'independent negative'},
 'descriptor_lifetime':{'good':'valid lifecycle scenario','bad':'pending-update negative with recovery','pending-reset':'pending-reset negative with recovery','stale-submit':'stale-submit negative with recovery','wrong-output':'oracle negative'},
 'pipeline_interface':{'bad-type':'injected interface defect','good':'minimal patch verified','missing-binding':'independent interface negative','wrong-output':'oracle negative'},
 'image_compute':{'missing-upload-dependency':'injected dependency defect','good':'minimal patch verified','bad-layout':'independent layout negative','missing-readback-dependency':'independent dependency negative','wrong-output':'oracle negative'},
 'tool_capture':{'bad':'authored invalid buffer negative','good':'valid buffer tool-capture case'}}
GAPS_ZH=['仅CPU软件ICD及coherent内存；noncoherent、移动GPU与性能收益未验证。','单队列、受限shader/格式/尺寸；不代表全部Vulkan或SC能力。','SyncVal shader-access为静态heuristic；关闭时未诊断的失败证据保留，不算PASS。','Perfetto记录CPU子进程耗时，不是GPU计时；不同链不构造资源或时序因果关联。','规范VUID查表成功不证明根因、修复充分性或条件全部适用。','未完成外部工程盲测、真实模型对照、全域语义验收或最终封板。','进程控制仅本次同group后代；不覆盖setsid逃逸、GPU挂死或device-loss。']
GAPS_EN=['CPU software ICD and coherent memory only; noncoherent visibility, mobile GPUs and performance gains remain unverified.','Single queue and bounded shaders/formats/extents; not all Vulkan or SC capability coverage.','SyncVal shader accesses use a static heuristic. The disabled-heuristic miss remains non-PASS.','Perfetto measures CPU subprocess duration, not GPU time; no cross-chain resource or causal timeline join.','A normative VUID match does not establish root cause, sufficient repair or every condition of applicability.','External blind engineering tasks, real-model comparisons, complete semantic acceptance and final release gates remain open.','Process control covers this group only, not setsid escape, GPU hangs or device loss.']

def digest(data):return hashlib.sha256(data).hexdigest()

def engine_next_check(stage, reason, result):
    """Suggest a discriminating observation for one scoped engine event."""
    if stage == 'submit' and result == 'rejected':
        return 'Inspect the submit return code and recording branch before checking presentation.'
    if stage in ('present_request', 'display_feedback') and reason:
        return 'Verify the output generation, linked submission and independent display feedback.'
    if stage == 'display_feedback':
        return 'Compare actual output pixels with composition, alpha and color-space settings.'
    if stage == 'present_request':
        return 'Obtain display feedback for this request; API acceptance alone does not show display.'
    if reason:
        return 'Obtain the missing source, stream or submission identity at the recorded call site.'
    return None

def safe_relative(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_./-]+',value):raise ValueError('nonportable artifact path')
    p=pathlib.PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or not p.parts:raise ValueError('unsafe artifact path')
    return p

def safe_file(root,relative):
    if root.is_symlink():raise ValueError('symlink root rejected')
    p=safe_relative(relative);path=root
    for part in p.parts:
        path=path/part
        if path.is_symlink():raise ValueError('symlink artifact rejected')
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():raise ValueError('artifact outside/missing')
    return path

def check_portable_text(data):
    text=data.decode('utf-8')
    if '\x00' in text or re.search(r'(?:/tmp/|/workspace/|/home/|[A-Za-z]:\\)',text):raise ValueError('nonportable/private absolute path in package text')
    return text

def add_artifact(root,relative,data,records,origin):
    safe_relative(relative);check_portable_text(data)
    if len(data)>1024*1024:raise ValueError('artifact exceeds minimal package size')
    dest=root/relative
    if dest.exists():raise ValueError('duplicate artifact path')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    records[relative]={'sha256':digest(data),'bytes':len(data),'origin':origin}

def source_allowlist():
    out=[]
    for chain in CASE_KINDS:
        if chain=='tool_capture':out+=['probes19/validation_probe.c']
        elif chain=='descriptor_lifetime':out += ['cases19/descriptor_lifetime/probe.c','cases19/descriptor_lifetime/compute.comp']
        else:
            out += [f'cases19/{chain}/baseline.c',f'cases19/{chain}/fix.patch']
            if chain!='transfer':out += [f'cases19/{chain}/compute.comp']
    return out

def raw_allowlist(reports):
    files=[]
    for chain,report in reports.items():
        for case in report['cases']:
            if chain=='transfer':files += [f'{chain}/{case}.json',f'{chain}/{case}.log']
            elif chain=='tool_capture':files += [f'{chain}/{case}.json']
            else:files += [f'{chain}/{case}.stdout',f'{chain}/{case}.stderr']
        if chain=='image_compute':files += [f'{chain}/heuristic-off.stdout',f'{chain}/heuristic-off.stderr']
    return files

def inline(value):
    # Prevent data strings from closing code spans or injecting HTML/Markdown.
    return str(value).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('`','&#96;').replace('\n',' ')

def plain_clause(text):
    class TextOnly(HTMLParser):
        def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
        def handle_data(self,data):self.parts.append(data)
    parser=TextOnly();parser.feed(text);parser.close();return ''.join(parser.parts)

def fenced_data(text):
    longest=max([len(s) for s in re.findall(r'`+',text)]+[2]);fence='`'*(longest+1)
    return [fence,text,fence]

def triage(index,reports,norm,language):
    uuid.UUID(index['run_id'])
    zh=language=='zh';lines=['# '+('诊断交付阅读包' if zh else 'Diagnostic handoff reading package'),'']
    lines += [('**限定结果：五条本地链的已记录证据经复核，不是最终能力验收。**' if zh else '**Bounded result: recorded evidence from five local chains was re-verified; this is not final capability acceptance.**'),'']
    lines += [('**来源：仓内作者主动注入的受控故障，不是外部生产工程发现的bug。**' if zh else '**Provenance: repository-authored deliberate fault injection, not a discovered external production bug.**'),'']
    lines += [f"Tests: `{inline(index['tests_head'])}`",f"Skill: `{inline(index['skill_head'])}`",f"Bundle run: `{inline(index['run_id'])}`",'']
    lines += [('读法：负控exit=0只表示预期检查完成，不表示被拒绝API成功；pipeline_result=-1000011001表示Validation回调中止。submitted=false时零数组仅是未提交占位，不是GPU渲染失败结果。' if zh else 'Legend: exit=0 on a negative control means the expected check completed, not that the rejected API succeeded. pipeline_result=-1000011001 means Validation callback abort. With submitted=false, zero arrays are unsubmitted placeholders, not failed GPU output.'),'']
    lines += ['## '+('事实、修复与负控' if zh else 'Facts, repairs and negative controls'),'']
    for chain,report in reports.items():
        lines += ['### '+chain,'']
        for case,kind in CASE_KINDS[chain].items():
            record=report['cases'][case];result=record.get('result',{})
            facts=[]
            if 'output' in result:facts.append(('unexecuted output placeholder=' if result.get('pipeline_result')==-1000011001 else 'output=')+str(result['output']))
            if 'first' in result:facts.append('readback='+str(result['first'])+'→'+str(result['second']))
            if 'pixels' in result:facts.append('unsubmitted pixel placeholders (not GPU output)' if result.get('submitted') is False else 'pixels='+json.dumps(result['pixels'],separators=(',',':')))
            for key in ('errors','submitted','pipeline_result'):
                if key in result:facts.append(key+'='+str(result[key]).lower())
            if 'matching_words' in record:facts.append('matching_words='+str(record['matching_words']))
            exit_code=result.get('exit_code',record.get('exit',record.get('exit_code')))
            facts.append('exit='+str(exit_code))
            lines.append(f'- `{case}`: {kind}; '+ '; '.join(facts)+'.')
        if chain in ('transfer','pipeline_interface','image_compute'):
            patch=f'sources/cases19/{chain}/fix.patch';lines += [f'- '+('实际最小补丁' if zh else 'Actually applied minimal patch')+f': [{patch}]({patch}).']
            repair=report.get('repair',{})
            before=repair.get('baseline_sha256',report['cases'].get('before',{}).get('source_sha256'))
            after=repair.get('fixed_sha256',report['cases'].get('after',{}).get('source_sha256'))
            lines += [f'- baseline SHA256: `{before}`',f'- fixed SHA256: `{after}`']
            meanings={'transfer':('启用transfer写→读内存依赖','Enable the transfer-write to transfer-read dependency'),'pipeline_interface':('将布局UBO类型修正为shader所需SSBO','Change the layout UBO descriptor type to the shader-required SSBO'),'image_compute':('启用上传transfer写→compute读取图像依赖','Enable uploaded-image transfer-write to compute-read dependency')}
            meaning=meanings[chain][0 if zh else 1]
            lines += ['- '+meaning+'.']
            lines += [('- 风险/回滚：只对该实验副本成立，不直接外推其他资源范围/队列；回到已哈希baseline.c可恢复故障fixture，不需git reset。外部工程回滚未测试，也未执行。' if zh else '- Risk/rollback: valid only for this fixture, not arbitrary resources or queues. Restoring the hashed baseline.c in a fresh fixture copy restores the injected defect; no git reset is needed. External-project rollback was neither executed nor validated.')]
            lines += [('- 复现：在原配对tests仓使用该链run.py及相同工具参数，选择新输出目录；阅读包本身不可独立运行。' if zh else '- Reproduce in the original paired tests checkout with this chain run.py, matching tools and a fresh output directory; the reading package is not standalone executable.')]
            lines += [f'  `python -O cases19/{chain}/run.py --include VULKAN_INCLUDE --loader VULKAN_LOADER '+('' if chain=='transfer' else '--tools TOOL_BIN ')+ '--output FRESH_OUTPUT`']
        elif chain=='descriptor_lifetime':lines += [('- 生命周期正反例与恢复行为；没有伪造独立patch。' if zh else '- Lifecycle scenarios and recovery behavior; no standalone patch is claimed.')]
        else:lines += [('- 输入size正反例与工具解析；不是patch修复证明。' if zh else '- Input-size controls and tool parsing, not a patch-repair proof.')]
        lines += ['']
    lines += ['## '+('实际诊断与精确规范对应' if zh else 'Observed diagnostics and exact normative lookup'),'']
    for item in norm['observations']:
        o=item['observation'];lookup=item['lookup'];path='evidence/'+str(safe_relative(o['logfile']));location=inline(f"{o['chain']}/{o['case']}, phase={o['phase']}, line={o['line']}")
        lines += [f"- `{inline(o['diagnostic'])}` · {location} · [{inline(lookup['status'])}]({path})"]
        for entry in lookup.get('normative_entries',[]):
            lines += [f"  - owner `{inline(entry['api_owner'])}`, condition `{inline(entry['condition_key'])}`, source page `{inline(entry['page'])}`."]
            lines += [('规范原文摘录（条件是否适用仍需人工复核）：' if zh else 'Normative excerpt (applicability still needs human review):')]
            lines += fenced_data(plain_clause(entry.get('text_html','')))

        if lookup['status']=='TOOL_DIAGNOSTIC':lines += [('  - 工具hazard，不伪造规范VUID条款。' if zh else '  - Tool hazard; no normative VUID clause is invented.')]
    lines += ['', '## '+('剩余缺口与交付边界' if zh else 'Remaining gaps and delivery boundaries'),'']
    lines += ['- '+x for x in (GAPS_ZH if zh else GAPS_EN)]
    lines += ['',('本包自包含阅读材料和哈希清单，但未包含全部二进制、完整规范、工具和原始bundle。离线hash校验仅证明清单内字节未变；重新执行与完整来源验收仍需要原bundle、配对仓库和工具。' if zh else 'This package contains self-contained reading evidence and a byte manifest, not all binaries, the full specification, tools or original bundle. Offline hash verification only checks package bytes against a trusted manifest digest. Re-execution and full provenance validation still need the original bundle, paired repositories and tools.'),'']
    return '\n'.join(lines)

def verify_package(root,expected_manifest_sha256,parse_json=json.loads):
    if not re.fullmatch('[0-9a-f]{64}',expected_manifest_sha256):raise ValueError('trusted external manifest SHA256 required')
    manifest_path=safe_file(root,'handoff-manifest.json');raw=manifest_path.read_bytes()
    if digest(raw)!=expected_manifest_sha256:raise ValueError('manifest digest mismatch')
    manifest=parse_json(raw)
    if manifest.get('status') not in ('VERIFIED_READING_PACKAGE','DEVELOPMENT_READING_PACKAGE') or manifest.get('schema_version')!=1:raise ValueError('unknown package schema/status')
    expected=manifest.get('files')
    if not isinstance(expected,dict) or not expected:raise ValueError('empty package')
    actual=set()
    for path in root.rglob('*'):
        if path.is_symlink():raise ValueError('symlink in package')
        if path.is_file():actual.add(str(path.relative_to(root)))
    if actual!=set(expected)|{'handoff-manifest.json'}:raise ValueError('missing or unexpected package files')
    for relative,record in expected.items():
        data=safe_file(root,relative).read_bytes();check_portable_text(data)
        if type(record.get('bytes')) is not int or len(data)!=record['bytes'] or digest(data)!=record['sha256']:raise ValueError('artifact modified: '+relative)
    return {'status':'PACKAGE_BYTES_VERIFIED_ONLY','manifest_sha256':expected_manifest_sha256,'files':len(expected),'not_verified':['execution','source repository identity without original bundle','normative correctness','final capability gates']}
