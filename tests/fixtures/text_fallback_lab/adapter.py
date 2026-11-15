"""Fixed trusted-face run shaper, not paragraph layout. Dedicated 24MiB TTC budget.
Original 16MiB platform_text_probe is unchanged. All face bytes and indices guarded.
"""
from __future__ import annotations
import ctypes as C
import ctypes.util
import hashlib
from pathlib import Path
FACES={
 'serif':('8cb29f7db250ebb2551a6ce2c1e0bfd5a0eb520e9e233370db0493e82e1f36f7',380660,0),
 'sans':('57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e',759720,0),
 'cjk':('b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a',19484784,2),
}
def guard(path,key):
 p=Path(path);digest,size,index=FACES[key]
 if not p.is_file() or p.stat().st_size!=size or size>24*1024*1024 or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('fixed trusted face mismatch before parsing')
 return index

class Info(C.Structure):
    _fields_=[('codepoint',C.c_uint32),('mask',C.c_uint32),('cluster',C.c_uint32),('var1',C.c_uint32),('var2',C.c_uint32)]
class Position(C.Structure):
    _fields_=[('x_advance',C.c_int32),('y_advance',C.c_int32),('x_offset',C.c_int32),('y_offset',C.c_int32),('var',C.c_uint32)]

def api():
    name=C.util.find_library('harfbuzz')
    if not name: raise RuntimeError('system HarfBuzz unavailable')
    h=C.CDLL(name); ptr=C.c_void_p; u=C.c_uint; i=C.c_int
    signatures={
        'hb_version_string':(C.c_char_p,[]),
        'hb_blob_create':(ptr,[C.c_char_p,u,i,ptr,ptr]),
        'hb_face_create':(ptr,[ptr,u]),'hb_face_get_upem':(u,[ptr]),
        'hb_face_get_glyph_count':(u,[ptr]),'hb_font_create':(ptr,[ptr]),
        'hb_font_set_scale':(None,[ptr,i,i]),'hb_ot_font_set_funcs':(None,[ptr]),
        'hb_buffer_create':(ptr,[]),'hb_buffer_allocation_successful':(i,[ptr]),
        'hb_buffer_add_utf8':(None,[ptr,C.c_char_p,i,u,i]),
        'hb_buffer_guess_segment_properties':(None,[ptr]),
        'hb_buffer_set_direction':(None,[ptr,i]),'hb_buffer_get_direction':(i,[ptr]),
        'hb_language_from_string':(ptr,[C.c_char_p,i]),'hb_buffer_set_language':(None,[ptr,ptr]),
        'hb_shape':(None,[ptr,ptr,ptr,u]),
        'hb_buffer_get_glyph_infos':(C.POINTER(Info),[ptr,C.POINTER(u)]),
        'hb_buffer_get_glyph_positions':(C.POINTER(Position),[ptr,C.POINTER(u)]),
    }
    for obj in ['blob','face','font','buffer']: signatures['hb_'+obj+'_destroy']=(None,[ptr])
    for n,(res,args) in signatures.items():f=getattr(h,n);f.restype=res;f.argtypes=args
    return h

def shape(font_path,text,*,direction='ltr',language='en',face_generation=1,max_utf8_bytes=128,key='serif'):
    face_index=guard(font_path,key)
    raw=text.encode('utf-8')
    if len(raw)>max_utf8_bytes: raise ValueError('text byte budget exceeded')
    if direction not in ('ltr','rtl'):raise ValueError('explicit run direction required')
    p=Path(font_path)
    if not p.is_file() or p.stat().st_size>24*1024*1024:raise ValueError('font missing or over budget')
    data=p.read_bytes();h=api(); objects=[]
    try:
        # DUPLICATE=0 copies bytes: no borrowed Python byte lifetime after this call.
        blob=h.hb_blob_create(data,len(data),0,None,None);objects.append(('blob',blob))
        face=h.hb_face_create(blob,face_index);objects.append(('face',face))
        upem=h.hb_face_get_upem(face);count=h.hb_face_get_glyph_count(face)
        if not upem or not count:raise ValueError('invalid or unsupported font face')
        font=h.hb_font_create(face);objects.append(('font',font));h.hb_ot_font_set_funcs(font);h.hb_font_set_scale(font,upem,upem)
        buf=h.hb_buffer_create();objects.append(('buffer',buf))
        h.hb_buffer_add_utf8(buf,raw,len(raw),0,len(raw));h.hb_buffer_set_direction(buf,4 if direction=='ltr' else 5)
        h.hb_buffer_set_language(buf,h.hb_language_from_string(language.encode(),-1));h.hb_buffer_guess_segment_properties(buf)
        h.hb_shape(font,buf,None,0)
        if not h.hb_buffer_allocation_successful(buf):raise MemoryError('HarfBuzz buffer allocation failed')
        n=C.c_uint();m=C.c_uint();infos=h.hb_buffer_get_glyph_infos(buf,C.byref(n));positions=h.hb_buffer_get_glyph_positions(buf,C.byref(m))
        if n.value!=m.value or n.value>16384:raise ValueError('glyph output budget/length')
        glyphs=[{'id':int(infos[j].codepoint),'cluster_utf8_byte':int(infos[j].cluster),'x_advance':int(positions[j].x_advance),'y_advance':int(positions[j].y_advance),'x_offset':int(positions[j].x_offset),'y_offset':int(positions[j].y_offset)} for j in range(n.value)]
        return {'provider':'linux-system-harfbuzz','provider_version':h.hb_version_string().decode(),'font_sha256':hashlib.sha256(data).hexdigest(),'face_index':face_index,'face_generation':face_generation,'variation_axes':{},'unit':'font_units','upem':upem,'direction':direction,'language':language,'glyphs':glyphs,'missing_glyphs':sum(g['id']==0 for g in glyphs),'fallback':'not_implemented','scope':'single run; no Android/Windows certification'}
    finally:
        for kind,obj in reversed(objects):getattr(h,'hb_'+kind+'_destroy')(obj)
