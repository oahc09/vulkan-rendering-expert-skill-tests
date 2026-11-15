"""Bounded actual FriBidi and independent ICU paragraph maps, fixed BMP input."""
import ctypes as C
TEXT='A سلام 12!'
def resolve(text,base):
 if base not in (0,1) or not text or len(text)>64 or any(ord(c)>0xffff or ord(c)<32 or 0x202a<=ord(c)<=0x202e or 0x2066<=ord(c)<=0x2069 for c in text):raise ValueError('bounded BMP paragraph input')
 h=C.CDLL('libfribidi.so.0');u=C.c_uint32;i=C.c_int;b=C.c_uint8
 h.fribidi_get_bidi_type.argtypes=[u];h.fribidi_get_bidi_type.restype=u
 h.fribidi_log2vis.argtypes=[C.POINTER(u),i,C.POINTER(u),C.POINTER(u),C.POINTER(i),C.POINTER(i),C.POINTER(b)];h.fribidi_log2vis.restype=b
 n=len(text);src=(u*n)(*map(ord,text));vis=(u*n)();l2v=(i*n)();v2l=(i*n)();levels=(b*n)();direction=u(h.fribidi_get_bidi_type(ord('A' if base==0 else 'א')))
 if not h.fribidi_log2vis(src,n,C.byref(direction),vis,l2v,v2l,levels):raise ValueError('FriBidi failed')
 if sorted(v2l)!=list(range(n)) or any(l2v[v2l[j]]!=j for j in range(n)):raise ValueError('bidi inverse map')
 return {'levels':list(levels),'visual_to_logical':list(v2l),'logical_to_visual':list(l2v)}
def icu(text,base):
 if base not in (0,1) or not text or len(text)>64 or any(ord(c)>0xffff or ord(c)<32 or 0x202a<=ord(c)<=0x202e or 0x2066<=ord(c)<=0x2069 for c in text):raise ValueError('bounded BMP paragraph input')
 h=C.CDLL('libicuuc.so.76');ptr=C.c_void_p;i=C.c_int32;u=C.c_uint16;b=C.c_uint8
 specs={'ubidi_open':(ptr,[]),'ubidi_close':(None,[ptr]),'ubidi_setPara':(None,[ptr,C.POINTER(u),i,b,C.POINTER(b),C.POINTER(i)]),'ubidi_getVisualMap':(None,[ptr,C.POINTER(i),C.POINTER(i)]),'ubidi_getLevels':(C.POINTER(b),[ptr,C.POINTER(i)])}
 for n,(res,args) in specs.items():f=getattr(h,n+'_76');f.restype=res;f.argtypes=args
 obj=h.ubidi_open_76();err=i(0);n=len(text);src=(u*n)(*map(ord,text));v=(i*n)()
 if not obj:raise MemoryError('ICU allocation')
 try:
  h.ubidi_setPara_76(obj,src,n,base,None,C.byref(err));h.ubidi_getVisualMap_76(obj,v,C.byref(err));lev=h.ubidi_getLevels_76(obj,C.byref(err))
  if err.value>0 or not lev:raise ValueError('ICU error')
  return {'levels':[int(lev[j]) for j in range(n)],'visual_to_logical':list(v)}
 finally:h.ubidi_close_76(obj)
def runs(text,base):
 if text!=TEXT:raise ValueError('only fixed audited paragraph supported')
 mapping=resolve(text,base);other=icu(text,base)
 if any(mapping[k]!=v for k,v in other.items()):raise ValueError('independent ICU bidi disagreement')
 result=[];start=0
 for end in range(1,len(text)+1):
  if end<len(text) and mapping['levels'][end]==mapping['levels'][start]:continue
  part=text[start:end];scripts=set('arabic' if '\u0600'<=c<='\u06ff' else 'latin' for c in part if c.isalpha())
  if len(scripts)>1:raise ValueError('multi-strong-script run unsupported')
  result.append({'start':start,'end':end,'text':part,'level':mapping['levels'][start],'direction':'rtl' if mapping['levels'][start]%2 else 'ltr','language':'ar' if scripts=={'arabic'} else 'en','visual_rank':min(mapping['logical_to_visual'][start:end])});start=end
 return sorted(result,key=lambda r:r['visual_rank']),mapping
