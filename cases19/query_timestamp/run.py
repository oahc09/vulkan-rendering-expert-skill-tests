"""Real ordinary timestamp lifecycle; CPU implementation timestamps, not GPU performance."""
import argparse,hashlib,json,os,pathlib,subprocess,uuid,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));import query19
SHA='f61afea8ca6097342cae1b65bfab81675ee7fdc2d809403e083329b7d56597a7'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 p=argparse.ArgumentParser();p.add_argument('--include',required=True);p.add_argument('--loader',required=True);p.add_argument('--validusage',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 require(sha(a.validusage)==SHA,'unpaired specification');spec=json.loads(pathlib.Path(a.validusage).read_text());entries={e['vuid']:e for group in spec['validation']['vkGetQueryPoolResults'].values() for e in group}
 lm=pathlib.Path(os.environ['VK_LAYER_PATH'])/'VkLayer_khronos_validation.json';layer=json.loads(lm.read_text())['layer'];require(layer['api_version']=='1.4.309','unpaired layer')
 source=pathlib.Path(__file__).with_name('probe.c');exe=a.output/'probe';r=subprocess.run(['gcc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+a.include,str(source),a.loader,'-o',str(exe)],capture_output=True,timeout=60)
 (a.output/'build.stdout').write_bytes(r.stdout);(a.output/'build.stderr').write_bytes(r.stderr);require(r.returncode==0,'compile failed')
 report={'run_id':str(uuid.uuid4()),'source_sha256':sha(source),'runner_sha256':sha(__file__),'rules_sha256':sha(query19.__file__),'binary_sha256':sha(exe),'loader_sha256':sha(a.loader),'icd_manifest_sha256':sha(os.environ['VK_DRIVER_FILES']),'layer_manifest_sha256':sha(lm),'spec_sha256':SHA,'spec_version':spec['version info'],'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'cases':{}}
 ids={'stride':'VUID-vkGetQueryPoolResults-flags-00815','size':'VUID-vkGetQueryPoolResults-dataSize-00817','partial':'VUID-vkGetQueryPoolResults-queryType-09439'}
 identity=None
 for mode in ('good','stride','size','partial'):
  r=subprocess.run([str(exe),mode],capture_output=True,timeout=30);(a.output/(mode+'.stdout')).write_bytes(r.stdout);(a.output/(mode+'.stderr')).write_bytes(r.stderr);require(r.returncode==0,'probe failed '+mode)
  rows=[json.loads(x) for x in r.stdout.decode().splitlines()];rec={x['kind']:x for x in rows};require(len(rows)==len(rec),'duplicate records');i=rec['identity'];require(i['deviceType']==4 and i['layerSpec']==4210997 and i['layerImplementation']==int(layer['implementation_version']) and i['timestampValidBits']>0 and i['timestampPeriod']>0,'identity mismatch')
  if identity is None:identity=i
  require(identity==i,'runtime changed');require(rec['unwritten']['result']==1 and rec['unwritten']['availability']==[0,0],'reset completion/poll failed');require(rec['fill']['words']==1024 and rec['fill']['memoryFlags']&6==6,'fill oracle/coherency');require(rec['completed']['fenceCompleted'] is True and rec['completed']['resetCompleted'] is True and all(x>0 for x in rec['completed']['availability']),'completion failed');require(rec['final']=={'kind':'final','errors':int(mode!='good'),'rc':0},'cleanup/errors')
  require(r.stderr.decode().splitlines()==([] if mode=='good' else [mode+' '+ids[mode]]),'unexpected diagnostics')
  config=rec.get('negative',rec['get_config']);require(config['flags'] in (5,13),'unknown result flags');rules=query19.layout(width=64 if config['flags']&1 else 32,count=config['queryCount'],stride=config['stride'],data_size=config['dataSize'],availability=bool(config['flags']&4),partial=bool(config['flags']&8))
  require(rules['vuids']==([ids[mode]] if mode!='good' else []),'rule mismatch')
  if mode!='good':require(config['result']==-1000011001,'callback did not abort')
  ident={'run':report['run_id'],'device':'cpu0','pool':mode,'queue':str(i['queueFamily']),'generation':1};obs={**ident,'reset_completed':True,'writes_completed':True,'values':rec['completed']['values'],'availability':rec['completed']['availability']}
  interpretation=query19.consume(identity=ident,observation=obs,valid_bits=i['timestampValidBits'],period_ns=i['timestampPeriod'],same_clock=True,upper_bound_ns=None,result_width=64)
  wc=rec['write_config'];require(wc['poolType']==2 and wc['queries']==[0,1] and wc['stages']==[1,8192],'write manifest mismatch');write_rules=[query19.write_admission(valid_bits=i['timestampValidBits'],pool_type='timestamp' if wc['poolType']==2 else 'unknown',pool_count=wc['poolCount'],query=q,reset_executed=wc['resetCompleted'],already_written=wc['alreadyWritten'],stage_supported=stage in (1,8192)) for q,stage in zip(wc['queries'],wc['stages'])]
  require(all(x['status']=='WRITE_WITHIN_SCOPE' for x in write_rules),'write rules mismatch')
  report['cases'][mode]={'range_rules':query19.query_range(pool_count=config['poolCount'],first_query=config['firstQuery'],count=config['queryCount']),'write_rules':write_rules,'records':rec,'exit_code':r.returncode,'diagnostics':r.stderr.decode().splitlines(),'layout_rules':rules,'interpretation':interpretation,'normative':entries[ids[mode]] if mode!='good' else None,'stdout_sha256':sha(a.output/(mode+'.stdout')),'stderr_sha256':sha(a.output/(mode+'.stderr'))}
 report['status']='BOUNDED_QUERY_LIFECYCLE_PASS';report['limitations']=['CPU ICD implementation timestamps, not physical GPU performance or pure fill time.','No independently justified elapsed upper bound: actual timestamp duration remains UNKNOWN_WRAP.','Generation stale-result rejection is CPU policy, not an additional device experiment.','No host-reset/occlusion/performance/calibrated timestamp/multiqueue coverage.','Original deliberate API misuse; callback aborts before invalid driver call.']
 (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
