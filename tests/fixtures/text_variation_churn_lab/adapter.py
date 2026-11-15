"""Linux system HarfBuzz probe. Not Android TextShaper/JNI or DirectWrite.

Uses only an explicitly supplied local font; never downloads/distributes fonts.
This trusted-fixture single-run adapter does no paragraph bidi, line layout or fallback.
Input/output count checks are not CPU-time or peak-memory isolation. Do not use
untrusted external fonts here: those require a separate process with timeout and
resource limits. This probe does not implement such a sandbox.
API basis: https://harfbuzz.github.io/a-simple-shaping-example.html
"""
from __future__ import annotations
import ctypes as C
import ctypes.util
import hashlib
import math
import freetype
from pathlib import Path

class Info(C.Structure):
    _fields_=[('codepoint',C.c_uint32),('mask',C.c_uint32),('cluster',C.c_uint32),('var1',C.c_uint32),('var2',C.c_uint32)]
class Position(C.Structure):
    _fields_=[('x_advance',C.c_int32),('y_advance',C.c_int32),('x_offset',C.c_int32),('y_offset',C.c_int32),('var',C.c_uint32)]

class Variation(C.Structure):
    _fields_=[("tag",C.c_uint32),("value",C.c_float)]

def coordinates(face, overrides):
    axes=face.get_variation_info().axes
    known={a.tag:a for a in axes}
    if not isinstance(overrides,dict) or any(k not in known for k in overrides):raise ValueError("unknown axis")
    values=[]
    for a in axes:
        v=overrides.get(a.tag,a.default)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not a.minimum<=v<=a.maximum:raise ValueError("invalid axis coordinate")
        # FT16.16 and HB float32 must represent the same coordinate exactly.
        if v*65536!=round(v*65536) or C.c_float(v).value!=v:raise ValueError("coordinate precision")
        values.append(float(v))
    return axes,values

def api():
    name=C.util.find_library('harfbuzz')
    if not name: raise RuntimeError('system HarfBuzz unavailable')
    h=C.CDLL(name); ptr=C.c_void_p; u=C.c_uint; i=C.c_int
    signatures={
        'hb_version_string':(C.c_char_p,[]),
        'hb_font_set_variations':(None,[ptr,C.POINTER(Variation),u]),
        'hb_font_get_var_coords_design':(C.POINTER(C.c_float),[ptr,C.POINTER(u)]),
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

def shape(font_path,text,*,direction='ltr',language='en',face_generation=1,max_utf8_bytes=4096,variation_axes=None):
    raw=text.encode('utf-8')
    if len(raw)>max_utf8_bytes: raise ValueError('text byte budget exceeded')
    if direction not in ('ltr','rtl'):raise ValueError('explicit run direction required')
    p=Path(font_path)
    if not p.is_file() or p.stat().st_size>16*1024*1024:raise ValueError('font missing or over budget')
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!='94a7ea95ccee28c54885a507e3cc0a534ce41ec61d413935df0e07261a7ffe63':raise ValueError('untrusted fixture font hash')
    ft=freetype.Face(str(p));axes,values=coordinates(ft,{} if variation_axes is None else variation_axes);ft.set_var_design_coords(values);ft_read=list(ft.get_var_design_coords())
    if ft_read!=values:raise ValueError("FT coordinate mismatch")
    h=api(); objects=[]
    try:
        # DUPLICATE=0 copies bytes: no borrowed Python byte lifetime after this call.
        blob=h.hb_blob_create(data,len(data),0,None,None);objects.append(('blob',blob))
        face=h.hb_face_create(blob,0);objects.append(('face',face))
        upem=h.hb_face_get_upem(face);count=h.hb_face_get_glyph_count(face)
        if not upem or not count:raise ValueError('invalid or unsupported font face')
        font=h.hb_font_create(face);objects.append(('font',font));h.hb_ot_font_set_funcs(font);h.hb_font_set_scale(font,upem,upem)
        variations=(Variation*len(axes))(*(Variation(int.from_bytes(a.tag.encode('ascii'),'big'),v) for a,v in zip(axes,values)))
        h.hb_font_set_variations(font,variations,len(axes));axis_count=C.c_uint();axis_ptr=h.hb_font_get_var_coords_design(font,C.byref(axis_count))
        if axis_count.value!=len(axes) or not axis_ptr:raise ValueError('HB coordinate count mismatch')
        hb_read=[float(axis_ptr[j]) for j in range(axis_count.value)]
        if hb_read!=values:raise ValueError('HB coordinate mismatch')
        buf=h.hb_buffer_create();objects.append(('buffer',buf))
        h.hb_buffer_add_utf8(buf,raw,len(raw),0,len(raw));h.hb_buffer_set_direction(buf,4 if direction=='ltr' else 5)
        h.hb_buffer_set_language(buf,h.hb_language_from_string(language.encode(),-1));h.hb_buffer_guess_segment_properties(buf)
        h.hb_shape(font,buf,None,0)
        if not h.hb_buffer_allocation_successful(buf):raise MemoryError('HarfBuzz buffer allocation failed')
        n=C.c_uint();m=C.c_uint();infos=h.hb_buffer_get_glyph_infos(buf,C.byref(n));positions=h.hb_buffer_get_glyph_positions(buf,C.byref(m))
        if n.value!=m.value or n.value>16384:raise ValueError('glyph output budget/length')
        glyphs=[{'id':int(infos[j].codepoint),'cluster_utf8_byte':int(infos[j].cluster),'x_advance':int(positions[j].x_advance),'y_advance':int(positions[j].y_advance),'x_offset':int(positions[j].x_offset),'y_offset':int(positions[j].y_offset)} for j in range(n.value)]
        return {'provider':'linux-system-harfbuzz','provider_version':h.hb_version_string().decode(),'font_sha256':hashlib.sha256(data).hexdigest(),'face_index':0,'face_generation':face_generation,'variation_axes':dict(zip([a.tag for a in axes],values)),'hb_design_coordinates':hb_read,'ft_design_coordinates':ft_read,'unit':'font_units','upem':upem,'direction':direction,'language':language,'glyphs':glyphs,'missing_glyphs':sum(g['id']==0 for g in glyphs),'fallback':'not_implemented','scope':'single run; no Android/Windows certification'}
    finally:
        for kind,obj in reversed(objects):getattr(h,'hb_'+kind+'_destroy')(obj)
