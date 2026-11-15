"""Single-owner bounded caches. No native face retention or GPU resources."""
from collections import OrderedDict
from copy import deepcopy
from time import perf_counter_ns

class Cache:
 def __init__(self, provider, entries=16, byte_budget=8192):
  if type(entries) is not int or type(byte_budget) is not int or not 1<=entries<=1024 or not 1<=byte_budget<=16777216: raise ValueError('positive budgets required')
  self.p=provider;self.entries=entries;self.limit=byte_budget
  self.layouts=OrderedDict();self.glyphs=OrderedDict();self.bytes=0;self.peak=0;self.times={'shape':[],'raster':[],'request':[]}
 def clear(self):
  self.layouts.clear();self.glyphs.clear();self.bytes=0
 def request(self,text,px=20,language='en',generation=1):
  if type(px) is not int or not 1<=px<=64 or type(generation) is not int or generation<1:raise ValueError('size/generation outside fixed domain')
  if not isinstance(text,str) or not text or len(text.encode())>64 or language not in ('en','fr'):raise ValueError('unsupported run')
  start=perf_counter_ns();lk=(self.p.identity,generation,text,'ltr',language)
  if lk not in self.layouts:
   t=perf_counter_ns();r=self.p.shape(text,language,generation);self.times['shape'].append(perf_counter_ns()-t)
   if any(g['id']==0 for g in r['glyphs']):raise ValueError('missing glyph')
   self.layouts[lk]=deepcopy(r)
   while len(self.layouts)>self.entries:self.layouts.popitem(last=False)
  self.layouts.move_to_end(lk);r=self.layouts[lk];result=[]
  for g in r['glyphs']:
   key=(self.p.identity,generation,g['id'],px,'gray-normal','no-axes','no-style','phase0')
   if key not in self.glyphs:
    t=perf_counter_ns();value=self.p.raster(g['id'],px);self.times['raster'].append(perf_counter_ns()-t)
    n=len(value['pixels'])
    if n>self.limit:raise ValueError('coverage byte budget exceeded')
    while self.glyphs and (len(self.glyphs)>=self.entries or self.bytes+n>self.limit):
     _,old=self.glyphs.popitem(last=False);self.bytes-=len(old['pixels'])
    self.glyphs[key]=deepcopy(value);self.bytes+=n;self.peak=max(self.peak,self.bytes)
   self.glyphs.move_to_end(key);result.append(deepcopy(self.glyphs[key]))
  self.times['request'].append(perf_counter_ns()-start)
  return deepcopy(r),result
