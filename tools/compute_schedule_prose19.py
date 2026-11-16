"""Frozen raw specification references, not expanded normative dependency closure."""
import hashlib,re
COMMIT='fa30d4e312e843193601be7cb926c7e25d9ec885'
SOURCES={
 'resources':('de7c50943e022c508b369a605ce05b20cc7376274d1e4ecb1d67234698732a7a',('resources-sharing',)),
 'features':('c3f4d376c6609c2ef14a7cc840fd0472167c2833fda0c5358d1f55e087b96ff2',('features',)),
 'fundamentals':('0e505b495d75fbe83029ac6e3c6451585f0eeef492224db0a3bbac1fd3217fa9',('fundamentals-queueoperation',)),
 'devsandqueues':('9a28a6b978bc4bf57fcaaf263488b4894129518be8aa2dc8b23269be43ade6ad',('devsandqueues-queueprops','devsandqueues-queue-creation','devsandqueues-submission')),
 'synchronization':('7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909',('synchronization-submission-order','synchronization-dependencies-memory'))}
def extract(name,raw):
 digest,anchors=SOURCES[name]
 if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('fixed368 prose hash mismatch')
 lines=raw.decode().splitlines(keepends=True);pos={}
 for i,line in enumerate(lines):
  m=re.fullmatch(r'\[\[([^\]]+)\]\]\s*',line)
  if m:pos[m[1]]=i
 slices=[]
 for anchor in anchors:
  start=pos[anchor];end=min([i for i in pos.values() if i>start] or [len(lines)])
  slices.append(dict(anchor=anchor,line_start=start+1,line_end=end,sha256=hashlib.sha256(''.join(lines[start:end]).encode()).hexdigest()))
 return dict(commit=COMMIT,path='chapters/'+name+'.adoc',sha256=digest,api_version='1.4.368',slices=slices,limitations='Raw source slices only; includes and conditionals not expanded. No VUID-derived performance claims.')
