"""Fail-closed verification of actual probe outputs, also under python -O."""
import csv,io,json
VUID='VUID-VkBufferCreateInfo-size-00912'
def callbacks(case, raw):
 data=json.loads(raw); ids=[x['pMessageIdName'] for x in data]
 if (case=='bad' and VUID not in ids) or (case=='good' and ids) or case not in ('bad','good'):
  raise ValueError('probe callback mismatch')
 return ids
def identity(stderr, manifest):
 lines=[x[9:] for x in stderr.decode().splitlines() if x.startswith('IDENTITY ')]
 if len(lines)!=1:raise ValueError('one runtime identity required')
 d=json.loads(lines[0]);parts=[int(x) for x in manifest['api_version'].split('.')]
 spec=(parts[0]<<22)|(parts[1]<<12)|parts[2]
 if d['device_type']!=4 or d['layer_spec']!=spec or d['layer_impl']!=int(manifest['implementation_version']):
  raise ValueError('runtime/manifest mismatch or non-CPU ICD')
 return d
def trace(raw,events):
 rows=list(csv.DictReader(io.StringIO(raw.decode())))
 if len(rows)!=len(events):raise ValueError('slice count mismatch')
 if len({r['id'] for r in rows})!=len(rows):raise ValueError('duplicate slice id')
 expected={e['name']:e for e in events}
 for row in rows:
  event=expected.pop(row['name'],None)
  if event is None:raise ValueError('unknown/duplicate event')
  if abs(int(row['ts'])-round(event['ts']*1000))>2000 or abs(int(row['dur'])-round(event['dur']*1000))>2000:
   raise ValueError('trace time mismatch')
 return True
